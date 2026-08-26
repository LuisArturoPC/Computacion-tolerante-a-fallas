# Computacion-tolerante-a-fallas
# (Par. 1) Otras herramientas para el manejar errores 

### Reporte: Herramientas y tecnologías para el manejo de errores en programación

| Categoría | Herramientas representativas | Función principal | Cómo previenen o gestionan fallos |
| :--- | :--- | :--- | :--- |
| **Estructuras de Control Nativo** | `try/catch/finally`, `Result<T, E>`, `Optional/Maybe`, códigos de estado (`Enums`) | Gestión del flujo de ejecución ante excepciones previstas. | Permiten aislar fragmentos propensos a fallos (I/O, red, parsing) y ejecutar rutas de recuperación sin romper el proceso principal. |
| **Monitoreo de Errores y Crash Reporting (APM)** | Sentry, Bugsnag, Rollbar, Datadog APM, Firebase Crashlytics | Captura de errores no controlados y caídas (*crashes*) en tiempo real. | Agrupan incidencias, registran el *stack trace*, capturan variables del entorno del usuario final y envían alertas inmediatas al equipo de desarrollo. |
| **Librerías y Frameworks de Logging** | Winston / Pino (Node.js), Loguru / logging (Python), Serilog (.NET), Log4j2 / SLF4J (Java) | Registro estructurado y persistente de eventos del sistema. | Permiten clasificar eventos por severidad (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`) y exportarlos a archivos locales o bases de datos indexables. |
| **Agregación y Análisis de Logs** | Stack Elastic (ELK), Grafana Loki, Splunk, Better Stack | Centralización y búsqueda masiva de registros. | Facilitan correlacionar trazas de errores distribuidos entre múltiples microservicios o servidores mediante dashboards y consultas avanzadas. |
| **Análisis Estático y Linters** | SonarQube, ESLint, Pylint / Flake8, Mypy, Clang-Tidy | Detección preventiva de vulnerabilidades y bugs potenciales. | Escanean el código fuente en tiempo de compilación o integración continua (CI/CD) para hallar punteros nulos, tipos incorrectos o fugas de memoria antes de producción. |
