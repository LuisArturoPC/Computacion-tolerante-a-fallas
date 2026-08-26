# Computacion-tolerante-a-fallas
# (Par. 2) Ejemplo: Otras herramientas para el manejar errores 

A continuación se detalla cada técnica implementada en el código fuente junto con su fragmento correspondiente:

---

### 1. Sistema de Logging Estructurado (`logging`)
Permite registrar eventos categorizados (`INFO`, `ERROR`, `CRITICAL`) tanto en la terminal como de forma persistente en un archivo de texto (`app_errors.log`).

```python
import logging

# Configuración de niveles, formato y destinos (archivo y consola)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app_errors.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
```

---

### 2. Excepciones Personalizadas (`Custom Exceptions`)
Permite definir un tipo de error propio derivado de `Exception` para representar fallos específicos de las reglas de negocio.

```python
class InventarioError(Exception):
    """Excepción personalizada para reglas de negocio."""
    pass
```

---

### 3. Aserciones (`assert`)
Verifica condiciones críticas o invariantes durante la fase de desarrollo. Si la condición no se cumple, detiene la ejecución arrojando un `AssertionError`.

```python
# Aserción para verificar que los datos internos no sean negativos
assert precio >= 0, "El precio no puede ser negativo"
```

---

### 4. Lanzamiento Manual de Excepciones (`raise`)
Dispara intencionalmente un error cuando las validaciones de entrada o del estado del inventario no se cumplen.

```python
# Validaciones de negocio en la función procesar_compra
if cantidad <= 0:
    raise ValueError("La cantidad a comprar debe ser un número entero mayor a 0.")
if cantidad > stock_disponible:
    raise InventarioError(f"Stock insuficiente. Solicitado: {cantidad}, Disponible: {stock_disponible}")
```

```python
# Validaciones en la captura de entradas por consola
if entrada_precio < 0:
    raise ValueError("El precio no puede ser negativo.")

if entrada_stock < 0:
    raise ValueError("El stock no puede ser negativo.")
```

---

### 5. Control de Flujo Completo (`try / except / else / finally`)
Encapsula el código propenso a fallos, captura errores puntuales para evitar la caída inesperada de la aplicación, ejecuta acciones tras un flujo exitoso (`else`) y asegura el cierre del ciclo (`finally`).

```python
try:
    logging.info("Iniciando transacción...")
    total = procesar_compra(precio, cantidad, stock)
except (ValueError, InventarioError) as err:
    logging.error(f"Fallo en la validación: {err}")
except Exception as err:
    logging.critical(f"Error inesperado del sistema: {err}", exc_info=True)
else:
    logging.info(f"Compra exitosa. Total a pagar: ${total:.2f}")
finally:
    logging.info("Finalizando intento de transacción.\n")
```

---

### 6. Captura de Interrupción del Usuario (`KeyboardInterrupt`)
Maneja de forma controlada la salida del script cuando el usuario presiona la combinación de teclas de interrupción manual (`Ctrl + C`).

```python
except KeyboardInterrupt:
    print("\nOperación cancelada por el usuario.")
```

---

### 7. Trazado de Pila Detallado (`exc_info=True`)
Agrega al registro de log el *stack trace* completo (línea y archivo exacto del fallo) para facilitar la depuración profunda ante fallos inesperados.

```python
except Exception as err:
    logging.critical(f"Error inesperado del sistema: {err}", exc_info=True)
```
