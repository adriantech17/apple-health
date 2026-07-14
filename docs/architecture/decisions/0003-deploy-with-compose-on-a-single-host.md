# ADR 0003: desplegar con Docker Compose en un único host

- Estado: aceptada
- Fecha: 2026-07-14

## Contexto

La instalación actual reside en una Raspberry Pi 5 con almacenamiento NVMe y
es operada por una sola persona. Docker y Docker Compose ya están disponibles.
No existe un requisito confirmado de alta disponibilidad ni despliegue en más
de un nodo.

## Decisión

Usar Docker Compose como unidad de despliegue en un único host.

El despliegue debe mantener:

- imágenes reproducibles y actualizadas mediante pull requests;
- procesos sin privilegios, capacidades mínimas y filesystem de solo lectura
  cuando sea viable;
- secretos montados como archivos, nunca incluidos en la imagen o el Git;
- health checks, límites de recursos y rotación de logs;
- volúmenes persistentes con propiedad y permisos documentados;
- copias cifradas, verificadas y almacenadas también fuera del host.

El acceso se limitará a una red de confianza. Antes de habilitar acceso remoto
o multiusuario se incorporará HTTPS mediante un reverse proxy pequeño o una
terminación TLS equivalente.

## Consecuencias

### Positivas

- operación y recuperación acordes con la escala real;
- configuración versionable sin versionar secretos;
- aislamiento suficiente para un host doméstico;
- despliegue reproducible sin operar un orquestador distribuido.

### Costes y límites

- la Raspberry Pi sigue siendo un único punto de fallo;
- Compose no proporciona alta disponibilidad entre nodos;
- la restauración depende de que las copias externas se prueben periódicamente.

## Alternativas descartadas

- **Kubernetes o Docker Swarm:** no existe una flota de nodos ni un requisito de
  disponibilidad que justifique su coste operativo.
- **Servicios cloud obligatorios:** reducirían el control local sobre datos de
  salud y añadirían gasto recurrente.
- **Instalación directa en el host:** dificulta reproducir dependencias y
  revertir versiones.

## Criterios de revisión

Revisar esta decisión si se exige continuidad ante la caída completa del host,
si la carga supera de forma sostenida los recursos disponibles o si el producto
se ofrece a usuarios externos con objetivos formales de disponibilidad.

## Referencias

- [Docker Compose: gestión de secretos](https://docs.docker.com/compose/how-tos/use-secrets/)
- [Docker: buenas prácticas de construcción](https://docs.docker.com/build/building/best-practices/)
- [FastAPI: HTTPS](https://fastapi.tiangolo.com/deployment/https/)
