# Arquitectura de Apple Health

Este directorio describe las decisiones técnicas que condicionan la evolución
del proyecto. Su objetivo es facilitar cambios coherentes, no convertir la
documentación en una especificación exhaustiva.

Los documentos distinguen deliberadamente entre:

- el sistema que existe hoy;
- la arquitectura objetivo aceptada;
- los criterios que justificarían revisar una decisión.

Una decisión aceptada no implica que su implementación haya finalizado.

## Contexto del producto

Apple Health es el nombre del proyecto: un dashboard privado para recibir,
conservar y analizar datos de la app Salud (Apple Health) exportados mediante
Health Auto Export.

En estos documentos se usa de forma consistente:

- **Apple Health**, para el proyecto;
- **app Salud (Apple Health)**, para la aplicación y plataforma de Apple;
- **Health Auto Export**, para la aplicación que realiza las exportaciones.

El alcance confirmado actualmente es:

- un usuario y una instalación privada;
- una Raspberry Pi 5 con almacenamiento NVMe;
- acceso desde la red local;
- importaciones semanales de métricas consolidadas;
- visualización de tendencias y explicación de patrones con contexto educativo,
  sin presentar el dashboard como herramienta diagnóstica;
- prioridad alta para privacidad, integridad y trazabilidad;
- posibilidad futura de incorporar usuarios y métricas adicionales, sin una
  previsión de escala o concurrencia confirmada.

La arquitectura debe resolver bien este alcance y permitir una evolución
gradual. Las hipótesis futuras no justifican por sí solas desplegar componentes
que todavía no son necesarios.

## Estado actual y arquitectura objetivo

La documentación describe una evolución, no un reemplazo inmediato. A fecha de
esta decisión, el sistema privado funciona con componentes que se simplificarán
de forma incremental:

| Responsabilidad | Implementación actual | Arquitectura objetivo |
|---|---|---|
| Interfaz | SPA con React, Vite y Recharts; backend for frontend (BFF) FastAPI separado | El mismo stack frontend servido por la aplicación modular |
| API | FastAPI y Uvicorn para ingesta y consultas | Monolito modular FastAPI con límites internos explícitos |
| Datos | SQLite para metadatos, Parquet para valores y DuckDB para consultas | Almacén operacional autoritativo; Parquet y DuckDB solo como capa analítica derivada |
| Despliegue | Docker Compose en Raspberry Pi, con dos contenedores de aplicación | Docker Compose con un desplegable de aplicación y proxy TLS al salir de la LAN de confianza |

Los manifiestos de dependencias y el código son la fuente de verdad para las
versiones instaladas. Los ADR justifican familias tecnológicas y fronteras
arquitectónicas, evitando quedar obsoletos con cada actualización menor.

## Principios

1. **Corrección antes que sofisticación.** Un valor de salud debe poder
   relacionarse con su importación y con las correcciones recibidas después.
2. **Privacidad por defecto.** Los datos, secretos y copias de seguridad no se
   versionan ni se envían a servicios externos por defecto.
3. **La solución más simple que cubra la carga medida.** Las decisiones de
   escalado se apoyan en métricas operativas, no en escenarios hipotéticos.
4. **Monolito modular antes que servicios distribuidos.** Los límites se
   mantienen en el código y solo se separan en despliegues cuando exista una
   necesidad operativa demostrable.
5. **Almacenamiento operacional y analítico con responsabilidades distintas.**
   Las escrituras transaccionales no dependen de un formato analítico.
6. **Cambios reversibles y trazables.** Las migraciones conservan versiones,
   incluyen validación y se integran mediante pull request.
7. **Operación asumible por una sola persona.** Cada servicio adicional debe
   compensar claramente su coste de actualización, monitorización y backup.
8. **Patrones explicables.** Una tendencia derivada debe indicar las métricas,
   el periodo y la regla que la sustentan, además de sus limitaciones.

## Arquitectura objetivo por responsabilidades

```mermaid
flowchart TD
    HAE["Health Auto Export"] --> APP["Aplicación FastAPI modular"]
    WEB["Dashboard React"] --> APP
    APP --> DB["Almacén operacional"]
    DB --> EXPORT["Exportación analítica por lotes"]
    EXPORT --> PARQUET["Parquet compactado"]
    PARQUET --> DUCKDB["Análisis con DuckDB"]
```

El diagrama representa responsabilidades, no servicios obligatoriamente
independientes. En la fase privada, la API y el dashboard pueden formar un
único desplegable. Parquet y DuckDB son opcionales y solo se incorporan a la
ruta analítica cuando el volumen o las consultas lo justifican.

## Evolución prevista

| Fase | Necesidad demostrada | Decisión mínima |
|---|---|---|
| Privada actual | Un usuario, carga semanal y consultas personales | Aplicación modular, un almacén operacional y Docker Compose |
| Perfiles locales | Pocos usuarios en la instalación privada y un único escritor | Incorporar identidad y autorización; mantener SQLite solo mientras las pruebas confirmen que sigue siendo suficiente |
| Multiusuario expuesto o concurrente | Acceso externo, escrituras multiproceso o varias réplicas | Migrar el almacén autoritativo a PostgreSQL antes de habilitar ese flujo |
| Analítica de volumen | Escaneos históricos grandes o muestras sin resumir | Generar Parquet compactado por lotes y consultar con DuckDB |
| Escala distribuida | Límites medidos de una única instancia | Evaluar réplicas o separación selectiva del componente limitante |

No se fija un número arbitrario de usuarios como frontera. La decisión debe
considerar simultáneamente concurrencia, frecuencia de escritura, volumen por
métrica, latencia observada, recuperación y coste operativo.

## Fuera de alcance

Mientras no exista evidencia que lo requiera, quedan fuera de la arquitectura:

- microservicios;
- Kubernetes;
- colas de mensajes;
- cachés distribuidas;
- particionamiento prematuro de bases de datos;
- una partición o archivo Parquet por usuario;
- infraestructura cloud obligatoria.

## Registro de decisiones

| ADR | Estado | Decisión |
|---|---|---|
| [0001](decisions/0001-use-a-modular-monolith.md) | Aceptada | Usar un monolito modular como arquitectura de aplicación |
| [0002](decisions/0002-use-a-react-spa.md) | Aceptada | Mantener una SPA con React, Vite y Recharts |
| [0003](decisions/0003-deploy-with-compose-on-a-single-host.md) | Aceptada | Desplegar con Docker Compose en un único host |
| [0004](decisions/0004-separate-operational-and-analytical-storage.md) | Aceptada | Separar el almacenamiento operacional del analítico |
| [0005](decisions/0005-govern-future-health-pattern-guidance.md) | Aceptada | Gobernar la futura orientación sobre patrones de salud mediante revisión fail-closed |

## Mantenimiento

Una decisión debe revisarse cuando cambie una restricción relevante, aparezcan
mediciones que contradigan sus supuestos o su coste operativo supere su
beneficio. El cambio se documentará en un ADR nuevo; los documentos anteriores
se conservarán para mantener el contexto histórico.
