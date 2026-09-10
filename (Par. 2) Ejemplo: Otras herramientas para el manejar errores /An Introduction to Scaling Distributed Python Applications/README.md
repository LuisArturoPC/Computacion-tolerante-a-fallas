
# Tolerancia a Fallos: Application Checkpointing Asíncrono

Técnica de tolerancia a fallos que captura el estado en memoria y lo guarda en disco (*Rollback / Restart*) de forma **no bloqueante**, permitiendo reanudar el sistema tras una caída sin reconfigurar datos ni perder progreso, mientras el bucle de eventos sigue atendiendo otras tareas.

---

## 1. Guardado de Checkpoint Asíncrono (`guardar_checkpoint_async`)

Permite escribir el estado crítico (precio y stock) en el archivo no volátil de forma asíncrona, utilizando `await` para pausar la corrutina y liberar el bucle de eventos (*Event Loop*) durante las operaciones de Entrada/Salida (I/O) en disco.

```python
async def guardar_checkpoint_async(precio, stock):
    """Persiste el estado en disco de forma asíncrona sin bloquear el flujo principal."""
    estado = {"precio": precio, "stock": stock}
    await asyncio.sleep(0.1)  # Simulación de latencia de I/O en almacenamiento

    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=4)

    logging.info(
        f"[CHECKPOINT ASÍNCRONO] Estado guardado: Precio=${precio:.2f}, Stock={stock}"
    )
```

* `async def ...`: Declara una corrutina que puede suspenderse y reanudarse.
* `estado = {...}`: Estructura los datos críticos en un diccionario.
* `await asyncio.sleep(0.1)`: Cede el control al *Event Loop* simulando la latencia de I/O.
* `open(..., "w")`: Abre el archivo sobrescribiendo versiones previas.
* `json.dump(...)`: Serializa los datos en disco de forma persistente.
* `logging.info(...)`: Registra la confirmación del guardado en bitácora.

---

## 2. Entrada de Datos No Bloqueante (`leer_input_async`)

Evita que la función sincrónica nativa `input()` congele la ejecución global del programa mientras el usuario escribe en la terminal, delegando la lectura a un hilo ejecutor mediante `run_in_executor`.

```python
async def leer_input_async(prompt: str) -> str:
    """Envuelve la lectura del teclado para no bloquear el bucle de eventos."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: input(prompt).strip().lower())
```

* `asyncio.get_running_loop()`: Obtiene el bucle de eventos activo en la corrutina actual.
* `run_in_executor(None, ...)`: Delega la llamada bloqueante a un hilo del *ThreadPoolExecutor* por defecto.
* `lambda: input(prompt)...`: Encapsula la lectura sincrónica y normaliza la entrada (`strip` + `lower`).
* `await ...`: Suspende la corrutina hasta que el hilo ejecutor devuelva el resultado, sin congelar el *Event Loop*.

---

## 3. Orquestador del Bucle de Eventos (`asyncio.run`)

Inicializa y gestiona el ciclo de vida del *Event Loop* en el punto de entrada del programa, permitiendo coordinar la ejecución continua de corrutinas asíncronas y capturar la detención forzada (`KeyboardInterrupt`).

```python
if __name__ == "__main__":
    try:
        # Inicio y gestión del bucle de eventos asíncrono
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n[FALLO SIMULADO] Proceso terminado abruptamente.")
        print("El estado quedó respaldado en el checkpoint.")
```

* `asyncio.run(...)`: Crea el *Event Loop*, ejecuta la corrutina principal y lo cierra al finalizar.
* `main_async()`: Corrutina raíz que orquesta el flujo asíncrono del programa.
* `except KeyboardInterrupt`: Atrapa el corte inmediato por terminal (`Ctrl + C`).
* `print(...)`: Notifica que la sesión cerró sin pasar por la salida limpia, dejando el checkpoint intacto.

---

## 4. Simulación de Caída Abrupta (`KeyboardInterrupt`)

Captura la interrupción manual del sistema para verificar que los datos en disco sobreviven a la falla, incluso cuando el guardado ocurre dentro del *Event Loop* asíncrono.

```python
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[FALLO SIMULADO] Proceso terminado abruptamente.")
        print("El estado quedó respaldado en el checkpoint.")
```

* `except KeyboardInterrupt`: Atrapa el corte inmediato por terminal (`Ctrl + C`).
* `print(...)`: Notifica que la sesión cerró sin pasar por la salida limpia, dejando el checkpoint intacto.
