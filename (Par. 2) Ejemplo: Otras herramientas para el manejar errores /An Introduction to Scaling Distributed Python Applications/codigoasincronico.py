import asyncio
import json
import logging
import os

CHECKPOINT_FILE = "checkpoint_tienda.json"

# Configuración de logging en consola y archivo .log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app_errors.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


class InventarioError(Exception):
    """Excepción personalizada para reglas de negocio."""

    pass


# ==========================================
# FUNCIONES ASÍNCRONAS DE CHECKPOINTING
# ==========================================
async def guardar_checkpoint_async(precio, stock):
    """Persiste el estado en disco de forma asíncrona sin bloquear el flujo principal."""
    estado = {"precio": precio, "stock": stock}
    # Simulamos una pequeña latencia de I/O
    await asyncio.sleep(0.1)

    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=4)

    logging.info(
        f"[CHECKPOINT ASÍNCRONO] Estado guardado: Precio=${precio:.2f}, Stock={stock}"
    )


def cargar_checkpoint():
    """Carga sincrónica al inicio para inicializar las variables antes del bucle de eventos."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                estado = json.load(f)
                logging.info(
                    "[CHECKPOINT] Estado previo detectado y recuperado exitosamente."
                )
                return estado["precio"], estado["stock"]
        except Exception as err:
            logging.error(
                f"[CHECKPOINT] Archivo corrupto o ilegible: {err}. Se iniciará desde cero."
            )
            return None
    return None


def resetear_checkpoint():
    """Borra el checkpoint para iniciar completamente desde cero."""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logging.info("[CHECKPOINT] Archivo de persistencia eliminado (Reset total).")


# ==========================================
# LÓGICA DE NEGOCIO Y LECTURA ASÍNCRONA
# ==========================================
async def leer_input_async(prompt: str) -> str:
    """Envuelve la lectura del teclado en un hilo secundario para no bloquear el bucle de eventos."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt).strip().lower())


def procesar_compra(precio, cantidad, stock_disponible):
    assert precio >= 0, "El precio no puede ser negativo"

    if cantidad <= 0:
        raise ValueError("La cantidad a comprar debe ser mayor a 0.")
    if cantidad > stock_disponible:
        raise InventarioError(
            f"No puedes comprar más del stock disponible (Intentaste comprar {cantidad} pero solo quedan {stock_disponible})."
        )

    return precio * cantidad


async def configurar_inicial_async():
    """Solicita la configuración inicial de forma asíncrona."""
    while True:
        try:
            raw_precio = await leer_input_async(
                "\nDefine el precio del producto: "
            )
            if raw_precio in ("exit", "salir"):
                return None, None
            precio = float(raw_precio)
            if precio < 0:
                raise ValueError("El precio no puede ser negativo.")

            raw_stock = await leer_input_async(
                "Define el stock inicial disponible: "
            )
            if raw_stock in ("exit", "salir"):
                return None, None
            stock_actual = int(raw_stock)
            if stock_actual < 0:
                raise ValueError("El stock no puede ser negativo.")

            await guardar_checkpoint_async(precio, stock_actual)
            return precio, stock_actual
        except ValueError as err:
            logging.error(f"Dato inicial inválido: {err}. Intenta de nuevo.")


async def reabastecer_producto_async(precio_actual):
    """Permite reponer stock y actualizar precio asíncronamente."""
    print("\n" + "=" * 45)
    print("      ¡EL STOCK SE HA AGOTADO POR COMPLETO!   ")
    print("=" * 45)

    nuevo_stock = 0
    while True:
        try:
            entrada_stock = await leer_input_async(
                "Ingresa la cantidad de nuevo stock a añadir (o 'exit' para salir): "
            )
            if entrada_stock in ("exit", "salir"):
                return None, None
            nuevo_stock = int(entrada_stock)
            if nuevo_stock <= 0:
                print(">> Debes ingresar al menos 1 unidad para continuar.")
                continue
            break
        except ValueError:
            print(">> Entrada inválida. Ingresa un número entero.")

    nuevo_precio = precio_actual
    while True:
        try:
            entrada_precio = await leer_input_async(
                f"Define el nuevo precio (Presiona ENTER para mantener ${precio_actual:.2f}): "
            )

            if entrada_precio == "":
                break
            if entrada_precio in ("exit", "salir"):
                return None, None

            precio_temporal = float(entrada_precio)
            if precio_temporal < 0:
                print(">> El precio no puede ser negativo.")
                continue

            nuevo_precio = precio_temporal
            break
        except ValueError:
            print(">> Entrada inválida. Ingresa un valor numérico.")

    await guardar_checkpoint_async(nuevo_precio, nuevo_stock)
    print(
        f"\n-> Producto reabastecido con éxito: Stock={nuevo_stock} | Precio=${nuevo_precio:.2f}\n"
    )
    return nuevo_precio, nuevo_stock


async def main_async():
    print("========================================")
    print("   SISTEMA DE GESTIÓN DE VENTAS (ASYNC) ")
    print("        (Con Checkpointing Activo)      ")
    print("  Comandos: 'exit' = salir | 'reset' = reiniciar")
    print("========================================")

    # 1. Recuperación de Checkpoint
    estado_recuperado = cargar_checkpoint()

    if estado_recuperado:
        precio, stock_actual = estado_recuperado
        print(
            f"\n-> Se restauró una sesión previa: Precio=${precio:.2f} | Stock={stock_actual}"
        )
    else:
        precio, stock_actual = await configurar_inicial_async()
        if precio is None:
            print("Programa finalizado.")
            return

    # 2. Bucle Asíncrono de Transacciones
    while True:
        if stock_actual == 0:
            precio, stock_actual = await reabastecer_producto_async(precio)
            if precio is None:
                print("Programa finalizado.")
                break

        print(
            f"\n--- ESTADO ACTUAL | Precio: ${precio:.2f} | Stock: {stock_actual} ---"
        )
        entrada = await leer_input_async("Cantidad a comprar ('reset' o 'exit'): ")

        if entrada in ("exit", "salir"):
            print("Cerrando el sistema. El estado quedó persistido en el checkpoint.")
            break

        if entrada in ("reset", "reiniciar"):
            confirmacion = await leer_input_async(
                "¿Seguro que deseas reiniciar todo a 0? (s/n): "
            )
            if confirmacion in ("s", "si", "sí", "y", "yes"):
                resetear_checkpoint()
                print(
                    "\n-> Sistema reiniciado por completo. Configura los nuevos valores iniciales:"
                )
                precio, stock_actual = await configurar_inicial_async()
                if precio is None:
                    print("Programa finalizado.")
                    break
                continue
            else:
                print("Reinicio cancelado.")
                continue

        try:
            cantidad = int(entrada)
            logging.info("Iniciando transacción asíncrona...")

            total = procesar_compra(precio, cantidad, stock_actual)
            stock_actual -= cantidad

            logging.info(f"Compra exitosa. Total a pagar: ${total:.2f}")
            logging.info(f"Nuevo stock restante: {stock_actual}")

            # 3. Guardado en disco asíncrono usando 'await'
            await guardar_checkpoint_async(precio, stock_actual)

        except ValueError as err:
            logging.error(f"Entrada no válida: {err}")
        except InventarioError as err:
            print(f"\n[AVISO DE STOCK] {err}\n")
            logging.warning(f"Intento fallido de compra: {err}")
        except Exception as err:
            logging.critical(f"Error inesperado del sistema: {err}", exc_info=True)
        finally:
            logging.info("Operación procesada.\n")


if __name__ == "__main__":
    try:
        # Inicio del bucle de eventos asíncrono
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n[FALLO SIMULADO] Proceso terminado abruptamente.")
        print("El estado quedó respaldado en el checkpoint.")
