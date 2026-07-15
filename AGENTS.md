# Instrucciones para agentes

Este archivo se aplica a todo el repositorio. No existen reglas más específicas
por subdirectorio; añade un `AGENTS.md` anidado solo cuando una carpeta tenga
necesidades estables y realmente distintas.

## Misión del proyecto

Apple Health es un dashboard privado para recibir, conservar y analizar
métricas consolidadas de la app Salud exportadas mediante Health Auto Export.
El alcance confirmado es una persona, una Raspberry Pi 5 con NVMe, acceso por
red local e importaciones semanales.

Prioriza, en este orden:

1. privacidad de los datos de salud;
2. corrección, trazabilidad y reversibilidad;
3. simplicidad operativa para un único mantenedor;
4. claridad de la experiencia y de las explicaciones;
5. rendimiento demostrado mediante mediciones.

No presentes el producto como una herramienta diagnóstica. Los patrones y
recomendaciones deben ser educativos, explicables y acompañarse de sus
limitaciones.

## Estado y fuentes de verdad

Trabaja sobre el estado real de la rama, no sobre funcionalidades mencionadas
como futuras. En `main`, el backend de ingesta está publicado y el dashboard y
el despliegue con Compose siguen una integración incremental.

Consulta solo lo necesario para la tarea y usa estas fuentes, por orden:

1. código, manifiestos y pruebas de la rama actual;
2. [decisiones de arquitectura](docs/architecture/README.md);
3. [README.md](README.md), para propósito, estado y uso;
4. [CONTRIBUTING.md](CONTRIBUTING.md), para el flujo de entrega.

Una ADR aceptada define una dirección, no confirma que la migración esté
terminada. Si el código y la documentación discrepan, no ocultes la diferencia:
detéctala, limita el cambio al scope solicitado y actualiza la documentación
aplicable.

## Privacidad: reglas no negociables

El repositorio es público. Trata todo archivo versionado, diff, comentario y log
como información pública.

- No leas, copies, transformes, subas ni versiones exportaciones reales de
  Salud salvo autorización explícita y un entorno privado adecuado.
- No añadas tokens, contraseñas, claves, `.env`, bases de datos, Parquet,
  backups, JSON comprimidos, rutas GPX ni capturas identificables.
- Usa fixtures mínimos y sintéticos; no anonimices superficialmente un export
  real para convertirlo en fixture.
- No muestres credenciales completas en terminales, errores, tests o ejemplos.
- No envíes datos de salud a APIs, telemetría o servicios externos por defecto.
- Si detectas un secreto, no lo repitas. Indica que debe rotarse y evita
  propagarlo a nuevos commits.
- Antes de cada commit, ejecuta `python scripts/check_repository.py` y revisa
  manualmente el diff.

## Límites arquitectónicos

La implementación actual usa FastAPI/Uvicorn, SQLite para metadatos, Parquet
para valores y DuckDB para consultas. La arquitectura objetivo es un monolito
modular con un almacén operacional autoritativo y una capa analítica derivada.

- Mantén límites de módulo claros sin convertirlos automáticamente en servicios
  de red.
- No introduzcas microservicios, Kubernetes, colas, cachés distribuidas ni
  infraestructura cloud obligatoria sin evidencia operativa y una ADR.
- No adoptes PostgreSQL solo por una posibilidad futura; sí reevalúalo antes de
  habilitar multiusuario expuesto, varios escritores o varias réplicas.
- No conviertas Parquet o DuckDB en fuente autoritativa multiusuario.
- No añadas una dependencia si una solución pequeña con el stack actual cubre
  el requisito. Justifica coste, mantenimiento y soporte ARM64.
- Mantén los tokens de ingesta y las futuras sesiones de usuario como
  credenciales distintas. El navegador nunca debe recibir el token de ingesta.
- Conserva `/health` como endpoint público mínimo; las rutas de datos deben
  exigir autenticación.

No implementes en una PR de producto toda la arquitectura objetivo de forma
incidental. Separa migraciones, infraestructura y cambios funcionales cuando
puedan validarse y revertirse de manera independiente.

## Corrección de los datos

Los cambios que afectan a métricas requieren especial cuidado:

- conserva la carga original y la relación entre observación e importación;
- mantén la idempotencia de payloads y no confundas una corrección con un
  duplicado;
- selecciona el valor vigente mediante una regla estable y probada, no por el
  orden del filesystem;
- agrupa días con `HEALTH_TIMEZONE`; no dependas de la zona local del proceso;
- conserva y normaliza unidades explícitamente, con pruebas de conversión;
- prueba fechas en límites de día y cambios de horario cuando sean relevantes;
- no promedies métricas aditivas ni sumes métricas de promedio sin definir
  primero su semántica;
- preserva los detalles necesarios para explicar mínimos, máximos, sueño y
  cualquier patrón derivado;
- no borres versiones, histórico o copias durante una migración de código.

Toda migración de almacenamiento debe ser reversible: requiere copia
verificada, comparación de equivalencia y un camino de vuelta antes de cambiar
las lecturas. Nunca ejecutes pruebas contra el dataset real.

## Forma de trabajar

1. Inspecciona `git status`, la rama y los archivos relevantes antes de editar.
2. Conserva cambios ajenos o no confirmados; no limpies el worktree de forma
   destructiva.
3. Expón supuestos que cambien el alcance y pregunta cuando la elección sea
   materialmente ambigua.
4. Implementa el cambio mínimo completo, con pruebas y documentación aplicable.
5. Usa una rama con un único objetivo y commits Conventional Commits con scope.
6. Revisa el diff completo y ejecuta las comprobaciones proporcionales al
   riesgo.
7. Publica mediante pull request. No hagas push directo a `main` ni fusiones una
   PR sin aprobación explícita del mantenedor, aunque la CI esté correcta.

Formatos aceptados:

```text
docs/project-guides
codex/docs-project-guides
docs(readme): document local API setup
```

Los detalles y todos los tipos admitidos están en
[CONTRIBUTING.md](CONTRIBUTING.md).

## Entorno y comprobaciones

Preparación del backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Validación obligatoria para cambios generales:

```bash
python -m pytest
python scripts/check_repository.py
python -m unittest scripts.test_check_repository
git diff --check
```

Para un cambio pequeño, ejecuta primero la prueba más cercana y después la
suite completa. No inventes comandos de lint, build o frontend: inspecciona los
manifiestos de la rama y usa únicamente scripts existentes. Si no puedes
ejecutar una comprobación, explica el motivo y el riesgo residual.

La validación de convenciones para una PR requiere rama, rango y título:

```bash
python scripts/check_conventions.py \
  --branch "$(git branch --show-current)" \
  --base origin/main \
  --head HEAD \
  --title "docs(project): add project documentation"
```

## Definición de terminado

Un cambio está listo para revisión cuando:

- cumple el objetivo sin ampliar el scope de forma silenciosa;
- conserva privacidad, autenticación e integridad del histórico;
- incluye pruebas relevantes con datos sintéticos;
- mantiene actualizados README, ADR o comentarios cuando cambie el contrato;
- pasa las comprobaciones locales aplicables y no introduce warnings ignorados;
- no contiene archivos generados, secretos ni datos personales;
- documenta riesgo, reversión y pasos manuales en la PR;
- deja la PR abierta para aprobación del mantenedor.

Al revisar, prioriza fugas de datos, errores de autenticación, pérdida de
versiones, zonas horarias, unidades, agregaciones y migraciones irreversibles
por encima de preferencias cosméticas.
