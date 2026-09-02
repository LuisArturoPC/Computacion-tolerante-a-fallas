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
# FUNCIONES DE CHECKPOINTING (Tolerancia a fallos)
# ==========================================
def guardar_checkpoint(precio, stock):
    """Guarda el estado consistente de la aplicación en disco."""
    estado = {"precio": precio, "stock": stock}
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=4)
    logging.info(f"[CHECKPOINT] Estado guardado: Precio=${precio:.2f}, Stock={stock}")


def cargar_checkpoint():
    """Intenta recuperar el estado previo tras un fallo o reinicio."""
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
# LÓGICA DE NEGOCIO
# ==========================================
def procesar_compra(precio, cantidad, stock_disponible):
    assert precio >= 0, "El precio no puede ser negativo"

    if cantidad <= 0:
        raise ValueError("La cantidad a comprar debe ser mayor a 0.")
    if cantidad > stock_disponible:
        raise InventarioError(
            f"No puedes comprar más del stock disponible (Intentaste comprar {cantidad} pero solo quedan {stock_disponible})."
        )

    return precio * cantidad


def configurar_inicial():
    """Solicita configuración inicial si no existe un checkpoint."""
    while True:
        try:
            raw_precio = input("\nDefine el precio del producto: ").strip().lower()
            if raw_precio in ("exit", "salir"):
                return None, None
            precio = float(raw_precio)
            if precio < 0:
                raise ValueError("El precio no puede ser negativo.")

            raw_stock = input("Define el stock inicial disponible: ").strip().lower()
            if raw_stock in ("exit", "salir"):
                return None, None
            stock_actual = int(raw_stock)
            if stock_actual < 0:
                raise ValueError("El stock no puede ser negativo.")

            guardar_checkpoint(precio, stock_actual)
            return precio, stock_actual
        except ValueError as err:
            logging.error(f"Dato inicial inválido: {err}. Intenta de nuevo.")


def reabastecer_producto(precio_actual):
    """Permite reponer stock y opcionalmente actualizar el precio cuando se agota."""
    print("\n" + "=" * 45)
    print("      ¡EL STOCK SE HA AGOTADO POR COMPLETO!   ")
    print("=" * 45)

    nuevo_stock = 0
    while True:
        try:
            entrada_stock = input("Ingresa la cantidad de nuevo stock a añadir (o 'exit' para salir): ").strip().lower()
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
            entrada_precio = input(
                f"Define el nuevo precio (Presiona ENTER para mantener ${precio_actual:.2f}): "
            ).strip()

            if entrada_precio == "":
                break
            if entrada_precio.lower() in ("exit", "salir"):
                return None, None

            precio_temporal = float(entrada_precio)
            if precio_temporal < 0:
                print(">> El precio no puede ser negativo.")
                continue

            nuevo_precio = precio_temporal
            break
        except ValueError:
            print(">> Entrada inválida. Ingresa un valor numérico.")

    guardar_checkpoint(nuevo_precio, nuevo_stock)
    print(f"\n-> Producto reabastecido con éxito: Stock={nuevo_stock} | Precio=${nuevo_precio:.2f}\n")
    return nuevo_precio, nuevo_stock


def main():
    print("========================================")
    print("      SISTEMA DE GESTIÓN DE VENTAS      ")
    print("        (Con Checkpointing Activo)      ")
    print("  Comandos: 'exit' = salir | 'reset' = reiniciar")
    print("========================================")

    # 1. Fase de Recuperación (Rollback / Restore)
    estado_recuperado = cargar_checkpoint()

    if estado_recuperado:
        precio, stock_actual = estado_recuperado
        print(
            f"\n-> Se restauró una sesión previa: Precio=${precio:.2f} | Stock={stock_actual}"
        )
    else:
        precio, stock_actual = configurar_inicial()
        if precio is None:
            print("Programa finalizado.")
            return

    # 2. Bucle de Transacciones
    while True:
        if stock_actual == 0:
            precio, stock_actual = reabastecer_producto(precio)
            if precio is None:
                print("Programa finalizado.")
                break

        print(f"\n--- ESTADO ACTUAL | Precio: ${precio:.2f} | Stock: {stock_actual} ---")
        entrada = input("Cantidad a comprar ('reset' o 'exit'): ").strip().lower()

        if entrada in ("exit", "salir"):
            print("Cerrando el sistema. El estado quedó persistido en el checkpoint.")
            break

        # Comando para reiniciar el sistema por completo
        if entrada in ("reset", "reiniciar"):
            confirmacion = input("¿Seguro que deseas reiniciar todo a 0? (s/n): ").strip().lower()
            if confirmacion in ("s", "si", "sí", "y", "yes"):
                resetear_checkpoint()
                print("\n-> Sistema reiniciado por completo. Configura los nuevos valores iniciales:")
                precio, stock_actual = configurar_inicial()
                if precio is None:
                    print("Programa finalizado.")
                    break
                continue
            else:
                print("Reinicio cancelado.")
                continue

        try:
            cantidad = int(entrada)
            logging.info("Iniciando transacción...")

            total = procesar_compra(precio, cantidad, stock_actual)
            stock_actual -= cantidad

            logging.info(f"Compra exitosa. Total a pagar: ${total:.2f}")
            logging.info(f"Nuevo stock restante: {stock_actual}")

            # 3. Fase de Checkpoint
            guardar_checkpoint(precio, stock_actual)

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
        main()
    except KeyboardInterrupt:
        print("\n\n[FALLO SIMULADO] Proceso terminado abruptamente.")
        print("El estado quedó respaldado en el checkpoint.")