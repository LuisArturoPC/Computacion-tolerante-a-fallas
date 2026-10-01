# Práctica: Orquestación de Flujos de Trabajo con Prefect

## 1. Introducción: ¿Qué es Prefect?

Prefect es un sistema moderno de gestión de flujos de trabajo en Python. Resuelve el problema de la automatización de procesos asumiendo la "ingeniería negativa": se encarga de la infraestructura, los reintentos, el manejo de caídas y el registro de eventos para que el desarrollador solo deba concentrarse en la lógica de negocio (ingeniería positiva).

Su filosofía *"Task Failed Successfully"* establece que el fallo de una tarea no debe colapsar el sistema, sino tratarse como un estado manejable con el que el orquestador puede reaccionar.

## 2. Parte 1: Estructura Básica (Mi Primer Flujo)

Este ejercicio demuestra la sintaxis fundamental de Prefect utilizando los decoradores `@task` y `@flow`. Se orquesta un flujo sencillo compuesto por dos tareas independientes que son supervisadas por el motor de Prefect para registrar su éxito de ejecución.

**Código fuente (`mi_primer_flow.py`):**

```python
from prefect import flow, task

@task
def saludar():
    print("Hola, estoy ejecutando mi primera tarea con Prefect.")

@task
def sumar():
    resultado = 10 + 20
    print(f"El resultado de la suma es: {resultado}")
    return resultado

@flow
def mi_primer_flujo():
    saludar()
    sumar()

if __name__ == "__main__":
    mi_primer_flujo()
```

## 3. Parte 2: Proceso ETL Avanzado (API JSONPlaceholder)

En este escenario práctico, se implementa un flujo de Extracción, Transformación y Carga (ETL). El orquestador extrae un catálogo de publicaciones desde una API externa (Cypress), filtra los registros para asegurar su integridad y finalmente carga los datos procesados en un archivo físico `.csv`. Se añaden parámetros de tolerancia a fallos (`retries=2`) para mejorar la resistencia del sistema contra interrupciones de red.

**Código fuente (`prefect_jsonplaceholder.py`):**

```python
import requests
import csv
from prefect import flow, task

URL = "https://jsonplaceholder.cypress.io/posts"

@task(retries=2, retry_delay_seconds=2)
def obtener_publicaciones():
    print("Conectando a la API de Cypress...")
    respuesta = requests.get(URL, timeout=30)
    respuesta.raise_for_status()
    publicaciones = respuesta.json()
    print(f"Se obtuvieron {len(publicaciones)} publicaciones.")
    return publicaciones

@task
def procesar_publicaciones(publicaciones):
    # Filtra solo los posts que tengan título y cuerpo válido
    validas = [
        post for post in publicaciones
        if post.get("title") and post.get("body")
    ]
    print(f"Publicaciones válidas: {len(validas)}")
    return validas

@task
def generar_reporte(publicaciones):
    nombre_archivo = "reporte_publicaciones.csv"

    # Generar archivo CSV
    with open(
        nombre_archivo,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:
        campos = ["id", "userId", "title", "body"]
        escritor = csv.DictWriter(
            archivo,
            fieldnames=campos,
            extrasaction="ignore"
        )
        escritor.writeheader()
        escritor.writerows(publicaciones)

    print(f"[*] Reporte guardado con éxito en: {nombre_archivo}")
    print("\n--- Primeras cinco publicaciones ---")

    for post in publicaciones[:5]:
        print(f'{post["id"]}: {post["title"]}')

    print("------------------------------------")
    return nombre_archivo

@flow(name="Analisis_Cypress_JSONPlaceholder")
def analizar_publicaciones():
    datos = obtener_publicaciones()
    datos_validos = procesar_publicaciones(datos)
    generar_reporte(datos_validos)

if __name__ == "__main__":
    analizar_publicaciones()
```

## 4. Instalación y ejecución

### Requisitos

* Python 3.10 o superior.
* Conexión a Internet.
* Un editor de código, como Visual Studio Code.

### Instalar las dependencias

Ejecutar el siguiente comando en la terminal:

```bash
pip install -U prefect requests
```

### Ejecutar la Parte 1

```bash
python mi_primer_flow.py
```

### Ejecutar la Parte 2

```bash
python prefect_jsonplaceholder.py
```

Al finalizar la segunda ejecución, se generará el archivo `reporte_publicaciones.csv`, que contendrá las publicaciones obtenidas y procesadas.

**Nota:** Si la API de Cypress no responde en la dirección configurada, se puede probar la URL alternativa `https://jsonplaceholder.typicode.com/posts`.

## 5. Resultados esperados

Al ejecutar los programas, se espera obtener los siguientes resultados:

* **Parte 1:** mensajes de saludo y el resultado de la suma (`30`).
* **Parte 2:** cantidad de publicaciones obtenidas, cantidad de registros válidos, títulos de las primeras cinco publicaciones y confirmación de la generación del archivo CSV.
* **Orquestación:** ejecución de las tareas mediante Prefect y registro de sus estados y eventos.

Los resultados concretos dependerán de que la instalación, la conexión a Internet y las solicitudes a la API funcionen correctamente.

## 6. Conclusión

El uso de Prefect permite organizar y automatizar scripts de Python transformándolos en flujos de trabajo más resistentes a los errores. Mediante la implementación de decoradores, el código adquiere capacidades de reintento, registro de eventos (*logs*) y control estructurado del flujo de datos.

En esta práctica se utilizaron dos ejemplos: uno básico para comprender el funcionamiento de los flujos y las tareas, y otro basado en una API para realizar un proceso ETL de extracción, transformación y carga de información en un archivo CSV.

Esto demuestra cómo Prefect puede facilitar la automatización de procesos en proyectos de análisis e ingeniería de datos, donde la organización, el seguimiento y la fiabilidad de las ejecuciones son importantes.
