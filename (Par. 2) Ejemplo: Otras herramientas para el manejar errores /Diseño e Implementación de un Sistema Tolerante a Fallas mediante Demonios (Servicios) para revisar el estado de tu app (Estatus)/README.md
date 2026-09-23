# Tolerancia a Fallas: Monitor de Servicio de Ventas (Watchdog Daemon)

Implementación de un sistema tolerante a fallos compuesto por dos procesos independientes: un **servicio principal** (Proceso A) que gestiona las ventas de una tienda, y un **demonio monitor** (Proceso B) que lo vigila en segundo plano y lo reinicia automáticamente si detecta una caída inesperada.

---

## Propuesta del Escenario

### 1. El problema que se desea resolver

Los sistemas de ventas en tiempo real son susceptibles a interrupciones abruptas. Si el proceso principal colapsa debido a un error de ejecución o una entrada no controlada, la tienda queda inoperante. Esto genera pérdida de datos en el inventario y requiere una intervención manual para volver a levantar el servicio, lo cual reduce drásticamente la disponibilidad del sistema.

El objetivo es garantizar que el servicio **siempre esté disponible**, reiniciándose automáticamente cuando falle y recuperando su último estado válido desde un archivo de checkpoint, sin intervención humana.

---

### 2. Por qué requiere ejecución en segundo plano

Es indispensable separar el sistema interactivo de su mecanismo de recuperación. Se requiere un **Demonio (monitor) en segundo plano** que opere de forma aislada y paralela al hilo del usuario. Si el monitor operara dentro del mismo proceso de la tienda, una falla crítica destruiría a ambos simultáneamente, imposibilitando la autorecuperación.

Al estar en segundo plano, el monitor:

- **Sobrevive** a la caída del servicio principal.
- **Monitorea continuamente** (bucle infinito con `subprocess.wait()`) sin bloquear la operación normal del Proceso A.
- Puede **reiniciar al servicio**, registrar eventos en un log persistente y manejar señales del sistema (`SIGINT`, `SIGTERM`) sin afectar la lógica de negocio.

---

### 3. Qué tipo de falla podría ocurrir

| Falla | Descripción | Cómo se detecta |
|-------|-------------|-----------------|
| **Excepciones críticas** | Errores lógicos graves o corrupciones de memoria que obligan al intérprete a cerrar el programa de golpe (situación que el sistema simula al teclear el comando `falla`). | `returncode != 0` |
| **Terminación anormal del proceso** | Interrupciones donde el proceso muere y devuelve al sistema operativo un código de salida distinto a cero (ej. `sys.exit(1)`). | `returncode != 0` |
| **Volatilidad de datos** | Pérdida de los valores almacenados en la memoria RAM (como la cantidad de stock disponible) al cerrarse la aplicación inesperadamente. | Recuperación vía checkpoint |
| **Apagado limpio intencional (`Ctrl+C`)** | El usuario decide cerrar el servicio; el proceso devuelve código `0` y el monitor **no debe reiniciarlo**, distinguiendo una salida legítima de una falla real. | `returncode == 0` |
| **Corrupción del archivo de checkpoint** | El JSON puede quedar truncado si el sistema muere a mitad de escritura; el servicio lo detecta con `try/except` y arranca con valores por defecto en lugar de colapsar. | `except Exception` en `cargar_checkpoint()` |

---

### 4. Qué estrategia de tolerancia se aplicará

Se aplica una estrategia de **recuperación automática** basada en cinco pilares:

#### a) Arquitectura Watchdog (Monitor de Procesos)

Se divide la solución en el **Proceso A (Tienda)** y el **Demonio B (Monitor)**. El monitor encapsula la ejecución de la tienda usando el módulo `subprocess` y se bloquea a la espera de su finalización. Si detecta que el proceso A terminó con un código de error, registra el evento en una bitácora y lanza una nueva instancia del servicio automáticamente.

#### b) Application Checkpointing (Persistencia de Estado)

El Proceso A guarda las variables de entorno (`precio` y `stock`) en un archivo físico (`estado_tienda.json`) después de cada transacción exitosa. Cuando el monitor reinicia el sistema tras una caída, el programa lee este archivo de respaldo para restaurar el inventario, logrando que la falla sea imperceptible para la continuidad del negocio.

#### c) Manejo de Señales del Sistema

Ambos procesos capturan `KeyboardInterrupt` (equivalente a `SIGINT`):

- En el **servicio**, un `Ctrl+C` produce una salida limpia con código `0`.
- En el **monitor**, un `Ctrl+C` detiene el bucle de supervisión sin dejar procesos huérfanos.

Esto permite diferenciar una **falla** (código ≠ 0 → reinicia) de un **apagado intencional** (código = 0 → termina).

#### d) Registro Persistente de Eventos

El monitor escribe todos los eventos relevantes en `monitor.log` mediante `logging.FileHandler`, incluyendo:

- Inicio de vigilancia.
- Caídas detectadas con su código de error.
- Reinicios aplicados.
- Apagados limpios.

Adicionalmente, el servicio persiste su estado de negocio en `estado_tienda.json` tras cada transacción, sirviendo como bitácora funcional del inventario.

#### e) Mitigación de Reinicios en Bucle (Anti-Flapping)

Antes de relanzar el servicio, el monitor espera **3 segundos** (`time.sleep(3)`). Esto evita ciclos infinitos de reinicio si el servicio falla inmediatamente al arrancar, dando tiempo a que condiciones transitorias se estabilicen.

---

### Flujo de Operación

```
┌─────────────────┐        lanza        ┌──────────────────────┐
│  monitor.py     │ ──────────────────► │  servicio_ventas.py  │
│  (Demonio B)    │                     │  (Proceso A)         │
│                 │ ◄──── wait() ─────  │                      │
└─────────────────┘                     └──────────────────────┘
        │                                         │
        │ returncode != 0 → reinicia              │ guarda checkpoint
        │ returncode == 0 → termina               │ tras cada venta
        ▼                                         ▼
   monitor.log                            estado_tienda.json
```

---

## Código del Demonio Monitor (`monitor.py`)

Vigila al servicio principal en un bucle infinito. Si detecta una salida con código distinto de cero, aplica tolerancia a fallos reiniciando el servicio tras una breve espera. Si el servicio sale limpiamente, termina la supervisión.

```python
import subprocess
import time
import logging
import sys

logging.basicConfig(
    filename="monitor.log",
    level=logging.INFO,
    format="%(asctime)s - [MONITOR] - %(levelname)s - %(message)s"
)
logging.getLogger("").addHandler(logging.StreamHandler())

def iniciar_demonio(script_objetivo):
    logging.info(f"Vigilando el servicio: {script_objetivo}")

    while True:
        proceso = subprocess.Popen([sys.executable, script_objetivo])

        try:
            proceso.wait()
        except KeyboardInterrupt:
            logging.info("Apagado manual (Ctrl+C) detectado en el monitor. Cerrando supervisor.")
            break

        if proceso.returncode != 0:
            logging.error(f"Caída detectada (Código de error {proceso.returncode}).")
            logging.info("Aplicando tolerancia a fallas: Reiniciando en 3 segundos...")
            time.sleep(3)
        else:
            logging.info("Servicio cerrado correctamente por el usuario. Apagando monitor.")
            break

if __name__ == "__main__":
    iniciar_demonio("servicio_ventas.py")
```

- `logging.basicConfig(...)`: Configura el log persistente en `monitor.log` con formato de fecha, nivel y mensaje.
- `logging.getLogger("").addHandler(...)`: Agrega un `StreamHandler` para que los eventos también se vean en consola.
- `iniciar_demonio(...)`: Función principal del demonio, recibe el script a vigilar.
- `subprocess.Popen([...])`: Lanza el servicio como un proceso hijo independiente usando el mismo intérprete de Python.
- `proceso.wait()`: Bloquea al monitor hasta que el proceso hijo termine, sin consumir CPU.
- `except KeyboardInterrupt`: Captura `Ctrl+C` para cerrar el monitor sin dejar procesos huérfanos.
- `proceso.returncode != 0`: Detecta una caída anormal (falla real).
- `time.sleep(3)`: Mitigación anti-flapping antes de reiniciar.
- `proceso.returncode == 0`: Distingue un apagado limpio intencional → detiene el monitor.

---

## Código del Servicio Principal (`servicio_ventas.py`)

Implementa la lógica de negocio de la tienda con **Application Checkpointing**. Carga el estado previo desde disco al arrancar, guarda el estado tras cada transacción válida y permite simular una caída abrupta con el comando `falla` para probar al monitor.

```python
import sys
import json
import os

CHECKPOINT_FILE = "estado_tienda.json"

def cargar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                estado = json.load(f)
                return estado["precio"], estado["stock"]
        except Exception:
            pass
    return 150.0, 20

def guardar_checkpoint(precio, stock):
    estado = {"precio": precio, "stock": stock}
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=4)

def main():
    print("--- [PROCESO A] Sistema de Ventas Iniciado ---")
    precio, stock = cargar_checkpoint()

    while True:
        try:
            print(f"\n>> ESTADO: Precio=${precio:.2f} | Stock={stock} unidades")
            entrada = input("¿Cuántas unidades desea comprar? (Escribe 'falla' para error, 'reset' para reiniciar stock): ").strip()

            if entrada.lower() == 'falla':
                print("\n[!] FATAL ERROR: Simulando caída abrupta del sistema...")
                sys.exit(1)
                
            if entrada.lower() == 'reset':
                precio, stock = 150.0, 20
                guardar_checkpoint(precio, stock)
                print("\n[+] REINICIO COMPLETO: El stock ha vuelto a 20 unidades.")
                continue

            cantidad = int(entrada)
            
            if cantidad <= 0:
                print("Ingresa una cantidad mayor a 0.")
            elif cantidad <= stock:
                stock -= cantidad
                total = cantidad * precio
                guardar_checkpoint(precio, stock)
                print(f"[*] Venta exitosa. Total a pagar: ${total:.2f}. Checkpoint guardado.")
            else:
                print("[-] Stock insuficiente.")

        except ValueError:
            print("[-] Entrada inválida. Ingresa un número.")
        except KeyboardInterrupt:
            print("\n[i] Apagado manual (Ctrl+C). Saliendo limpiamente...")
            sys.exit(0)

if __name__ == "__main__":
    main()
```

- `CHECKPOINT_FILE`: Nombre del archivo donde se persiste el estado crítico.
- `cargar_checkpoint()`: Verifica si existe un estado previo y lo restaura; si está corrupto o no existe, retorna valores por defecto `(150.0, 20)`.
- `try/except Exception`: Evita que un JSON corrupto colapse el arranque del servicio.
- `guardar_checkpoint(...)`: Serializa `precio` y `stock` en disco sobrescribiendo la versión anterior.
- `sys.exit(1)`: Simula una caída abrupta al escribir `falla`, activando la tolerancia a fallos del monitor.
- `sys.exit(0)`: Salida limpia con `Ctrl+C`, el monitor la interpreta como apagado intencional.
- `int(entrada)` dentro de `try`: Captura entradas no numéricas sin colapsar el servicio.
- Bucle `while True`: Mantiene la tienda operativa hasta una falla, un `reset` o una salida limpia.

---

## Cómo Ejecutar

1. Abrir **dos terminales** en el directorio del proyecto.
2. En la primera terminal, iniciar el monitor:

```bash
python monitor.py
```

3. El monitor lanzará automáticamente el servicio. En la terminal verás la interfaz de la tienda.
4. Prueba los siguientes escenarios:

| Acción | Resultado esperado |
|--------|--------------------|
| Escribir `5` | Venta exitosa, checkpoint actualizado |
| Escribir `falla` | El servicio cae con código 1, el monitor lo reinicia en 3 segundos |
| Escribir `reset` | Stock vuelve a 20, checkpoint sobrescrito |
| Escribir `Ctrl+C` | Salida limpia, monitor termina sin reiniciar |

5. Revisar los archivos generados:

- `monitor.log` → bitácora persistente de eventos del demonio.
- `estado_tienda.json` → checkpoint del estado de negocio.
