# ADR 0001: usar un monolito modular

- Estado: aceptada
- Fecha: 2026-07-14

## Contexto

El producto funciona inicialmente para una persona en una Raspberry Pi. Debe
recibir exportaciones, autenticar el dashboard, consultar métricas y servir la
interfaz web. Existe intención de incorporar usuarios en el futuro, pero no hay
una escala ni una concurrencia confirmadas.

Separar estas responsabilidades en servicios de red independientes aumentaría
el número de imágenes, secretos, health checks, despliegues y puntos de fallo.
Ese coste no aporta hoy aislamiento operativo ni escalado independiente útil.

## Decisión

La arquitectura objetivo será un monolito modular construido con FastAPI:

- un único desplegable contendrá la API y los archivos estáticos del dashboard;
- ingestión, autenticación, consultas y análisis serán módulos explícitos;
- cada módulo tendrá interfaces y pruebas propias;
- los esquemas de autenticación de ingesta y usuario permanecerán separados;
- los módulos se comunicarán dentro del proceso, no mediante HTTP interno;
- se mantendrá un único propietario de la transacción de escritura.

La modularidad es una regla de código, no una obligación de distribuir el
sistema. Una sola aplicación puede ejecutarse en más de una réplica en el
futuro si el almacén operacional permite concurrencia entre procesos.

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

## Criterios de revisión

Revisar esta decisión si una medición demuestra que un módulo necesita escalar
o desplegarse de manera independiente, si aparece una frontera regulatoria o de
seguridad, o si distintos equipos requieren ciclos de entrega autónomos.

## Referencias

- [FastAPI: despliegue en contenedores](https://fastapi.tiangolo.com/deployment/docker/)
- [FastAPI: terminación HTTPS](https://fastapi.tiangolo.com/deployment/https/)
