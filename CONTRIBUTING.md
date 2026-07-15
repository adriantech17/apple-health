# Contribuir a Apple Health

Gracias por mejorar Apple Health. El proyecto maneja información especialmente
sensible, por lo que una contribución correcta debe ser pequeña, trazable,
probada y segura para el dataset existente.

## Antes de empezar

Lee, según el alcance del cambio:

- [README.md](README.md), para conocer el propósito y el estado real;
- [la documentación de arquitectura](docs/architecture/README.md), para
  entender las decisiones aceptadas;
- [AGENTS.md](AGENTS.md), si trabajas con Codex, Copilot, OpenCode u otro agente
  de programación.

Una decisión aceptada no debe implementarse completa de forma implícita en una
PR no relacionada. Si el cambio modifica una frontera arquitectónica, añade un
ADR nuevo o actualiza el estado mediante una decisión posterior. No reescribas
el contexto histórico de un ADR aceptado.

## Preparar el entorno

Se requiere Python 3.12 o posterior.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Las pruebas usan directorios temporales y credenciales sintéticas. No apuntes
la configuración de desarrollo al dataset real.

## Flujo de trabajo

Todo cambio llega a `main` mediante una rama y una pull request. El push directo
a `main` no forma parte del flujo normal.

1. Actualiza tu referencia local de `main`.
2. Crea una rama con un único objetivo.
3. Implementa cambios pequeños y coherentes con ese objetivo.
4. Añade o actualiza las pruebas y la documentación aplicables.
5. Ejecuta las comprobaciones locales.
6. Revisa el diff para descartar secretos y datos de salud.
7. Publica la rama y abre una pull request.
8. Espera a que la CI finalice correctamente y a la aprobación explícita del
   mantenedor antes de fusionar.

No existe un número mínimo obligatorio de revisores, pero una CI correcta no
autoriza por sí sola la fusión.

## Nombres de rama

La CI admite dos formatos:

```text
<tipo>/<descripcion-con-guiones>
<agente>/<tipo>-<descripcion-con-guiones>
```

Tipos admitidos:

```text
build chore ci docs feat fix perf refactor revert style test
```

Agentes admitidos en el segundo formato:

```text
codex copilot opencode
```

Ejemplos válidos:

```text
docs/project-guides
fix/123-correct-daily-timezone
codex/docs-project-guides
opencode/test-storage-retention
```

Usa minúsculas, números y guiones. La descripción debe contener al menos dos
segmentos para que exprese un scope reconocible.

## Commits convencionales

Cada commit debe seguir Conventional Commits con scope obligatorio:

```text
<tipo>(<scope>): <descripción imperativa>
```

Ejemplos:

```text
docs(readme): document local API setup
fix(storage): select the latest metric correction
test(api): cover oversized ingestion payloads
```

Reglas del repositorio:

- usa uno de los tipos de rama admitidos;
- escribe el tipo y el scope en minúsculas;
- limita el asunto a 100 caracteres;
- mantén un único propósito verificable por commit;
- incluye en el mismo commit las pruebas o documentación directamente
  necesarias para que ese cambio sea válido;
- no incluyas cambios de formato o refactors ajenos al scope.

El título de la pull request debe seguir el mismo formato y resumir el conjunto
completo de commits.

## Validación

Antes de publicar, ejecuta:

```bash
python -m pytest
python scripts/check_repository.py
python -m unittest scripts.test_check_repository
git diff --check
```

También puedes validar las convenciones de la rama y los commits contra
`origin/main`:

```bash
python scripts/check_conventions.py \
  --branch "$(git branch --show-current)" \
  --base origin/main \
  --head HEAD \
  --title "docs(project): add project documentation"
```

Sustituye el título de ejemplo por el título real de la pull request.

La CI vuelve a ejecutar la auditoría del repositorio, sus pruebas, la suite del
backend y la validación de convenciones. Si una comprobación no es aplicable,
explícalo en la PR; no ocultes ni ignores el fallo.

## Criterios para las pruebas

- reproduce primero un defecto con una prueba cuando sea viable;
- cubre casos válidos, límites y errores relevantes;
- utiliza `tmp_path`, payloads sintéticos y tokens de prueba;
- evita depender de la red, la hora local o servicios externos;
- comprueba explícitamente zona horaria, unidades, idempotencia y selección de
  correcciones cuando el cambio afecte a datos de salud;
- no reduzcas cobertura funcional para hacer pasar la CI.

El proyecto no impone todavía un porcentaje de cobertura: se valora la calidad
de las aserciones sobre una cifra aislada.

## Privacidad y seguridad

No añadas ni pegues en código, documentación, issues, logs o pull requests:

- exportaciones reales de Apple Health o Health Auto Export;
- capturas con información identificable;
- bases de datos, Parquet, JSON comprimidos o copias de seguridad;
- tokens, contraseñas, claves privadas o archivos `.env`;
- rutas de entrenamiento, ubicaciones o metadatos personales.

Usa exclusivamente fixtures mínimos y sintéticos. `scripts/check_repository.py`
actúa como barrera adicional, no como garantía de que un archivo sea seguro.

Si detectas una credencial expuesta, no la publiques en un issue. Rótala de
inmediato y comunica el incidente al mantenedor por un canal privado. Eliminar
el archivo del último commit no retira el secreto del historial.

## Cambios de dependencias y arquitectura

Una dependencia nueva debe resolver una necesidad concreta que no cubra de
forma razonable el stack actual. Documenta su coste operativo, mantenimiento y
compatibilidad con Raspberry Pi/ARM64.

- fija las dependencias directas de Python en `pyproject.toml`;
- conserva las acciones de GitHub fijadas por SHA;
- no introduzcas microservicios, colas, cachés distribuidas o Kubernetes sin
  evidencia operativa y un ADR que lo justifique;
- no conviertas Parquet o DuckDB en fuente autoritativa multiusuario;
- no ejecutes migraciones destructivas sobre el dataset existente;
- separa los cambios de infraestructura, producto y documentación cuando
  puedan revisarse de forma independiente.

## Pull requests

Completa la plantilla y deja claros:

- el objetivo y lo que queda fuera del scope;
- los cambios observables;
- las pruebas ejecutadas;
- el impacto sobre privacidad, datos y compatibilidad;
- el riesgo y el camino de reversión;
- cualquier migración o paso manual.

No fusiones una PR hasta que la CI esté correcta y el mantenedor haya dado su
aprobación explícita. Conserva los commits con sentido propio; no reescribas el
historial de una rama compartida sin coordinarlo.
