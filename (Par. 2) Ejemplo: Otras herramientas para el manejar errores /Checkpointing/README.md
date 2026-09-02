# Tolerancia a Fallos: Application Checkpointing

Técnica de tolerancia a fallos que captura el estado en memoria y lo guarda en disco (*Rollback / Restart*) para reanudar el sistema tras una caída sin reconfigurar datos ni perder progreso.

---

### 1. Persistencia de Estado (`guardar_checkpoint`)

Escribe las variables críticas en disco tras cada transacción válida para mantener sincronizado el estado.

```python
def guardar_checkpoint(precio, stock):
    estado = {"precio": precio, "stock": stock}
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=4)
    logging.info(f"[CHECKPOINT] Estado guardado: Precio=${precio:.2f}, Stock={stock}")
```

* `estado = {...}`: Estructura los datos críticos en un diccionario.
* `open(..., "w")`: Abre el archivo sobrescribiendo versiones previas.
* `json.dump(...)`: Serializa los datos en disco de forma persistente.
* `logging.info(...)`: Registra la confirmación del guardado en bitácora.

---

### 2. Recuperación tras Fallas (`cargar_checkpoint`)

Lee el archivo en el arranque para restaurar las variables y evitar la configuración manual, reduciendo el MTTR.

```python
def cargar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                estado = json.load(f)
                logging.info("[CHECKPOINT] Estado previo detectado y recuperado exitosamente.")
                return estado["precio"], estado["stock"]
        except Exception as err:
            logging.error(f"[CHECKPOINT] Archivo corrupto o ilegible: {err}. Se iniciará desde cero.")
            return None
    return None
```

* `os.path.exists(...)`: Valida si existe un respaldo previo antes de leer.
* `json.load(...)`: Deserializa el JSON e hidrata el estado en memoria.
* `return ...`: Inyecta el precio y stock recuperados al flujo de ejecución.
* `except Exception`: Previene caídas si el archivo fue interrumpido a medias.

---

### 3. Purgado Controlado (`resetear_checkpoint`)

Elimina físicamente el archivo del disco cuando se solicita reiniciar el entorno desde cero.

```python
def resetear_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logging.info("[CHECKPOINT] Archivo de persistencia eliminado (Reset total).")
```

* `os.remove(...)`: Destruye el respaldo previo para reiniciar en blanco.
* `logging.info(...)`: Documenta en el log que el borrado fue intencional.

---

### 4. Simulación de Caída Abrupta (`KeyboardInterrupt`)

Captura la interrupción manual del sistema para verificar que los datos en disco sobreviven a la falla.

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
