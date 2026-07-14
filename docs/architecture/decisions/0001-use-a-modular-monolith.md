# ADR 0001: usar un monolito modular

- Estado: Aceptada
- Fecha: 2026-07-14

## Contexto

El producto funciona inicialmente para una persona en una Raspberry Pi. Debe
recibir exportaciones, autenticar el dashboard, consultar métricas y servir la
interfaz web. Existe intención de incorporar usuarios en el futuro, pero no hay
una escala ni una concurrencia confirmadas.

La implementación desplegada separa temporalmente la ingesta y el BFF del
dashboard en dos procesos FastAPI. Ambos pertenecen al mismo producto, se
despliegan en el mismo host y comparten secretos de comunicación, por lo que esa
separación no constituye una frontera de seguridad independiente.

Separar estas responsabilidades en servicios de red independientes aumentaría
el número de imágenes, secretos, health checks, despliegues y puntos de fallo.
Ese coste no aporta hoy aislamiento operativo ni escalado independiente útil.

## Decisión

La arquitectura objetivo será un monolito modular construido con Python,
FastAPI y Uvicorn:

- un único desplegable contendrá la API y los archivos estáticos del dashboard;
- ingestión, autenticación, consultas y análisis serán módulos explícitos;
- cada módulo tendrá interfaces y pruebas propias;
- los esquemas de autenticación de ingesta y usuario permanecerán separados;
- el navegador usará una sesión `HttpOnly` del mismo origen y nunca recibirá el
  token de ingesta;
- los módulos se comunicarán dentro del proceso, no mediante HTTP interno;
- se mantendrá un único propietario de la transacción de escritura.

La modularidad es una regla de código, no una obligación de distribuir el
sistema. Una sola aplicación puede ejecutarse en más de una réplica en el
futuro si el almacén operacional permite concurrencia entre procesos.

## Justificación del stack backend

Python se mantiene porque la normalización, validación y futura analítica de
datos ya utilizan su ecosistema y cuentan con pruebas. Introducir otro runtime
en el backend duplicaría dependencias y conocimiento sin resolver una
limitación medida.

FastAPI proporciona validación declarativa, middleware y un modelo ASGI
adecuado para una API JSON pequeña. Uvicorn es suficiente como servidor en el
contenedor. En la Raspberry Pi se priorizará un proceso sencillo; se añadirán
workers o réplicas solo después de disponer de un almacén operacional apto para
concurrencia y de medir una saturación real.

Las operaciones analíticas que excedan el tiempo razonable de una petición se
ejecutarán primero como trabajos programados dentro del mismo proyecto. No se
introducirá una cola distribuida mientras un proceso por lotes sea suficiente.

Las versiones concretas se gestionan en `pyproject.toml` y se actualizan en
pull requests con CI; el ADR no fija versiones menores.

La contraseña única del dashboard es una solución exclusiva de la fase
privada, no el modelo de identidad multiusuario. Antes de admitir nuevas
cuentas se documentarán por separado autenticación, recuperación, revocación de
sesiones, autorización y protección CSRF para operaciones con estado. Las
cookies se marcarán `Secure` cuando exista HTTPS.

## Consecuencias

### Positivas

- despliegues y recuperación más sencillos;
- menos secretos y comunicación interna;
- transacciones y trazabilidad más fáciles de mantener;
- menor consumo de recursos en la Raspberry Pi;
- posibilidad de extraer un módulo más adelante sin diseñar microservicios hoy.

### Costes y límites

- un fallo del proceso puede afectar a todas las funciones;
- los límites de los módulos deben protegerse mediante estructura y pruebas;
- no permite escalar una responsabilidad de forma independiente sin separarla.

## Alternativas descartadas

- **Dos servicios FastAPI para dashboard e ingesta:** no crean una frontera de
  seguridad efectiva en el mismo host y duplican operación.
- **Microservicios:** no existen equipos, carga ni requisitos de disponibilidad
  que compensen la coordinación distribuida.
- **Funciones serverless:** añaden dependencia externa y contradicen el
  requisito actual de almacenamiento privado local.
- **Django:** su ORM, panel de administración y autenticación integrada serían
  útiles en otro tipo de producto, pero no compensan migrar una API funcional y
  un frontend independiente. Se reconsiderará si aparece un back-office como
  requisito central.
- **Node.js para el backend:** unificaría el lenguaje con el navegador, pero
  obligaría a sustituir una canalización Python probada sin una mejora operativa
  demostrada.

## Criterios de revisión

Revisar esta decisión si una medición demuestra que un módulo necesita escalar
o desplegarse de manera independiente, si aparece una frontera regulatoria o de
seguridad, o si distintos equipos requieren ciclos de entrega autónomos.

## Referencias

- [FastAPI: despliegue en contenedores](https://fastapi.tiangolo.com/deployment/docker/)
- [FastAPI: características](https://fastapi.tiangolo.com/features/)
- [FastAPI: terminación HTTPS](https://fastapi.tiangolo.com/deployment/https/)
