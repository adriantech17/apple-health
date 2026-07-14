# ADR 0002: mantener una SPA con React, Vite y Recharts

- Estado: aceptada
- Fecha: 2026-07-14

## Contexto

El dashboard es una aplicación interactiva privada. No necesita indexación por
buscadores, generación pública de páginas ni renderizado en el servidor. Sí
necesita gráficas temporales, navegación por métricas y una interfaz adaptable.

## Decisión

Mantener el frontend como SPA con React, Vite, Recharts y CSS convencional.

La evolución del código seguirá estas reglas:

- migrar a TypeScript de forma incremental, sin reescritura completa;
- mantener el catálogo de métricas separado de los componentes;
- aislar el cliente API y las transformaciones de datos;
- probar especialmente cálculos, unidades y transformaciones de salud;
- dividir el bundle solo cuando una medición indique un problema real;
- evitar estado global mientras el estado local y los hooks sean suficientes.

No se incorporarán por defecto un framework SSR, Redux, Tailwind ni un sistema
de componentes completo.

## Consecuencias

### Positivas

- stack pequeño, conocido y adecuado para la interacción requerida;
- desarrollo y compilación rápidos;
- gráficas declarativas integradas con los componentes React;
- tipado progresivo de estructuras de métricas heterogéneas.

### Costes y límites

- la aplicación depende de JavaScript en el navegador;
- la disciplina modular no viene impuesta por un framework;
- Recharts puede requerir optimización si aparecen series muy densas.

## Alternativas descartadas

- **Next.js u otro framework SSR:** sus capacidades principales no responden a
  una necesidad del dashboard privado.
- **HTML generado por el backend:** complicaría la interacción y las gráficas.
- **Una biblioteca de estado global:** no existe todavía estado compartido con
  complejidad suficiente para justificarla.

## Criterios de revisión

Revisar esta decisión si el producto pasa a necesitar páginas públicas con SEO,
renderizado en servidor, funcionamiento sin JavaScript o visualizaciones cuyo
volumen exceda de forma medida las capacidades de SVG y Recharts.

## Referencias

- [React 19.2](https://react.dev/blog/2025/10/01/react-19-2)
- [React: alternativas recomendadas a Create React App](https://react.dev/blog/2025/02/14/sunsetting-create-react-app)
- [Vite 8.1](https://vite.dev/blog/announcing-vite8-1)
- [Recharts: soporte de TypeScript](https://recharts.github.io/en-US/guide/typescript/)
