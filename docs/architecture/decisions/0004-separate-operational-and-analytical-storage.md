# ADR 0004: separar el almacenamiento operacional del analítico

- Estado: Aceptada
- Fecha: 2026-07-14

## Contexto

La implementación inicial usa SQLite para metadatos e índices, escribe valores
en Parquet mediante PyArrow y consulta esos archivos con DuckDB. Este diseño
preserva el histórico, pero distribuye una importación entre una transacción
SQLite y escrituras de archivos que no pueden confirmarse de forma atómica.

Una medición previa a la reconciliación histórica, realizada el 12 de julio de
2026, mostró 13.701 registros físicos en 13.601 archivos Parquet. Ese patrón de
casi un archivo por registro introduce coste de filesystem y escaneo sin
obtener las ventajas de archivos columnares grandes.

Actualmente se reciben agregados diarios para una persona. En el futuro pueden
existir más usuarios, métricas o muestras sin resumir. No se ha confirmado aún
su número, concurrencia ni tasa de escritura.

Para dimensionar la decisión, el número aproximado de valores vigentes es:

```text
usuarios × métricas × días
```

Con 25 métricas diarias y sin contar correcciones, cinco años representan:

| Usuarios | Valores vigentes aproximados |
|---:|---:|
| 1 | 45.625 |
| 100 | 4.562.500 |
| 1.000 | 45.625.000 |

Las versiones corregidas multiplican esas filas. Las muestras sin resumir
pueden aumentar el volumen varios órdenes de magnitud y son el escenario que
primero podría justificar almacenamiento columnar.

## Decisión

Separar dos responsabilidades:

1. El **almacén operacional** será la fuente autoritativa y transaccional.
2. El **almacén analítico** será derivado, reconstruible y generado por lotes.

### Etapa privada

SQLite será suficiente como almacén operacional mientras existan un usuario,
un único proceso propietario de las escrituras y una carga compatible con el
host. Una futura migración consolidará importaciones, versiones y valores
vigentes en la misma base de datos.

El modelo lógico deberá representar, como mínimo:

- `imports`, con origen, huella, fecha y resultado de cada carga;
- `metric_versions`, con todas las correcciones recibidas;
- una vista o proyección `metric_current` para el valor vigente;
- unidad, detalles JSON e identificador de importación;
- `user_id` antes de habilitar el primer usuario adicional.

Al introducir `user_id`, el histórico existente se asignará mediante una
migración explícita al propietario inicial; no se inferirá el propietario a
partir de nombres de dispositivo, fuentes o campos libres.

La selección del valor vigente se definirá mediante una regla estable y
probada, no mediante el orden incidental de los archivos. La idempotencia se
aplicará dentro del propietario del dato: una huella repetida para un usuario no
creará una segunda importación, pero no deduplicará datos entre usuarios.

### Etapa multiusuario

PostgreSQL sustituirá a SQLite como fuente autoritativa antes de ofrecer el
producto multiusuario fuera del entorno privado, aceptar escrituras
concurrentes desde varios procesos o ejecutar varias réplicas de la aplicación.
Un número pequeño de perfiles locales podría seguir usando SQLite únicamente
si conserva un solo escritor y las pruebas de carga y recuperación lo avalan.

Todas las claves, índices y consultas de salud incluirán `user_id`. El control
de acceso se aplicará en la aplicación: la identidad se obtendrá de la sesión o
credencial validada y nunca de un `user_id` libre enviado por el cliente. Los
tokens de importación pertenecerán a un usuario y no podrán escribir datos de
otro. Row-Level Security podrá añadirse como defensa adicional, acompañada de
pruebas específicas que eviten fugas entre usuarios.

El particionamiento de tablas solo se añadirá después de medir que las tablas o
sus tareas de mantenimiento lo necesitan. Incorporar PostgreSQL no implica
crear particiones desde el primer día.

### Etapa analítica

Parquet se conservará como opción para histórico analítico cuando el volumen o
las consultas lo justifiquen:

- se exportará desde el almacén operacional mediante un proceso por lotes;
- no será la única copia de ningún dato;
- los archivos serán compactos en número y grandes en tamaño;
- no se particionará por usuario;
- la granularidad temporal se elegirá a partir del tamaño medido;
- el dataset podrá eliminarse y reconstruirse.

DuckDB consultará ese dataset para análisis históricos, correlaciones o tareas
de ciencia de datos. No gestionará autenticación, sesiones ni escrituras
operacionales multiusuario. El dashboard consultará normalmente el almacén
operacional; los análisis costosos se ejecutarán de forma controlada y sus
resultados podrán persistirse para servirlos sin escanear Parquet en cada
petición.

Los archivos analíticos contienen los mismos datos sensibles que la base de
datos y mantendrán permisos, retención y protección equivalentes. No se
publicarán en almacenamiento externo por defecto.

Si los archivos generados no pueden alcanzar tamaños razonables o las consultas
operacionales siguen siendo rápidas, la capa Parquet no se desplegará.

## Transición desde la implementación actual

El cambio no será una migración destructiva ni un reemplazo directo:

1. crear una copia verificada del dataset;
2. implementar el nuevo esquema detrás de una interfaz de almacenamiento;
3. importar el histórico conservando importaciones y correcciones;
4. comparar por usuario, métrica y fecha valores, unidades y detalles;
5. cambiar las lecturas después de obtener equivalencia completa;
6. conservar un camino de reversión durante un periodo definido.

Los archivos actuales no se eliminarán como parte del cambio de código.

## Consecuencias

### Positivas

- escrituras operacionales atómicas;
- backups y restauraciones más sencillos;
- consultas por usuario y fecha con índices convencionales;
- una frontera explícita de propiedad para cada dato de salud;
- Parquet y DuckDB disponibles cuando aporten una ventaja medida;
- la analítica no condiciona la integridad del dato original.

### Costes y límites

- la evolución a PostgreSQL requerirá una migración explícita;
- la exportación analítica introduce una copia derivada que debe poder
  regenerarse;
- SQLite no es la opción final si aparecen varios procesos escritores.

## Alternativas descartadas

- **Mantener un archivo Parquet por observación:** escala el número de archivos,
  no el rendimiento analítico.
- **Usar DuckDB como base operacional multiusuario:** su modelo principal es
  analítico e integrado en proceso, no un servidor transaccional tradicional.
- **Adoptar PostgreSQL inmediatamente:** añade operación sin beneficio para la
  fase privada; se introducirá cuando la concurrencia, el aislamiento o la
  operación multiusuario lo justifiquen.
- **Eliminar Parquet y DuckDB para siempre:** impediría aprovecharlos si se
  incorporan muestras de alta frecuencia o análisis históricos grandes.

## Criterios de revisión

Activar PostgreSQL antes del primer flujo multiusuario expuesto fuera del
entorno privado, ante escrituras desde varios procesos o cuando se necesiten
réplicas. La migración se decidirá por concurrencia, aislamiento, operación y
recuperación, no solo por el recuento de usuarios.

Activar la exportación Parquet cuando los escaneos históricos afecten de forma
medida al almacén operacional, se incorporen grandes volúmenes de muestras sin
resumir o puedan generarse archivos compactados de tamaño útil. DuckDB
recomienda evitar particiones pequeñas y sitúa el rango ideal de cada archivo
Parquet entre 100 MB y 10 GB.

## Referencias

- [SQLite: usos apropiados](https://sqlite.org/whentouse.html)
- [DuckDB: concurrencia](https://duckdb.org/docs/current/connect/concurrency.html)
- [DuckDB: escrituras particionadas](https://duckdb.org/docs/lts/data/partitioning/partitioned_writes.html)
- [DuckDB: tamaños de archivos Parquet](https://duckdb.org/docs/lts/guides/performance/file_formats.html)
- [PostgreSQL: Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [PostgreSQL: particionamiento declarativo](https://www.postgresql.org/docs/current/ddl-partitioning.html)
