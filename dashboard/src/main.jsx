import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './styles.css'

const METRICS = [
  { id: 'step_count', label: 'Pasos', short: 'Pasos', unit: 'pasos', group: 'Actividad', color: '#5b6cff', icon: '↗', cadence: 'daily', decimals: 0, completeDaysOnly: true },
  { id: 'active_energy', label: 'Energía activa', short: 'Energía activa', unit: 'kcal', group: 'Actividad', color: '#ff6b67', icon: '✦', cadence: 'daily', decimals: 0, completeDaysOnly: true },
  { id: 'walking_running_distance', label: 'Distancia andando y corriendo', short: 'Distancia', unit: 'km', group: 'Actividad', color: '#24a47c', icon: '⌁', cadence: 'daily', decimals: 2, completeDaysOnly: true },
  { id: 'apple_exercise_time', label: 'Tiempo de ejercicio', short: 'Ejercicio', unit: 'min', group: 'Actividad', color: '#ef7654', icon: '◒', cadence: 'daily', decimals: 0, completeDaysOnly: true },
  { id: 'apple_stand_hour', label: 'Horas de pie', short: 'Horas de pie', unit: 'h', group: 'Actividad', color: '#38a6a5', icon: '│', cadence: 'daily', decimals: 0, completeDaysOnly: true },
  { id: 'apple_stand_time', label: 'Tiempo de pie', short: 'Tiempo de pie', unit: 'min', group: 'Actividad', color: '#58b7a6', icon: '╎', cadence: 'daily', decimals: 0, completeDaysOnly: true },
  { id: 'flights_climbed', label: 'Pisos subidos', short: 'Pisos', unit: 'pisos', group: 'Actividad', color: '#d68145', icon: '⇧', cadence: 'daily', decimals: 0, completeDaysOnly: true },

  { id: 'resting_heart_rate', label: 'Frecuencia cardiaca en reposo', short: 'FC reposo', unit: 'lpm', group: 'Corazón', color: '#eb4c78', icon: '♥', cadence: 'daily', decimals: 0 },
  { id: 'heart_rate_variability', label: 'Variabilidad de la frecuencia cardiaca', short: 'HRV', unit: 'ms', group: 'Corazón', color: '#a855f7', icon: '≈', cadence: 'daily', decimals: 1 },
  { id: 'vo2_max', label: 'Capacidad aeróbica', short: 'VO₂ máx.', unit: 'ml/kg/min', group: 'Corazón', color: '#396ee8', icon: '◌', cadence: 'sparse', decimals: 1 },
  { id: 'cardio_recovery', label: 'Recuperación cardiaca', short: 'Recuperación', unit: 'lpm', group: 'Corazón', color: '#d24e92', icon: '↘', cadence: 'sparse', decimals: 1 },
  { id: 'walking_heart_rate_average', label: 'Frecuencia cardiaca caminando', short: 'FC caminando', unit: 'lpm', group: 'Corazón', color: '#e36b87', icon: '♡', cadence: 'daily', decimals: 0 },
  { id: 'heart_rate', label: 'Frecuencia cardiaca diaria', short: 'FC diaria', unit: 'lpm', group: 'Corazón', color: '#f04464', icon: '⌁', cadence: 'daily', decimals: 0 },

  { id: 'respiratory_rate', label: 'Frecuencia respiratoria', short: 'Respiración', unit: 'resp/min', group: 'Respiración', color: '#12a4a6', icon: '◍', cadence: 'daily', decimals: 1 },
  { id: 'blood_oxygen_saturation', label: 'Oxígeno en sangre', short: 'SpO₂', unit: '%', group: 'Respiración', color: '#1687d9', icon: '○', cadence: 'daily', decimals: 1 },

  { id: 'sleep_analysis', label: 'Duración y fases del sueño', short: 'Sueño', unit: 'h', group: 'Sueño', color: '#665acb', icon: '☾', cadence: 'daily', decimals: 1 },

  { id: 'walking_speed', label: 'Velocidad al caminar', short: 'Velocidad', unit: 'km/h', group: 'Movilidad', color: '#3e9b78', icon: '➜', cadence: 'daily', decimals: 2 },
  { id: 'walking_step_length', label: 'Longitud del paso', short: 'Longitud paso', unit: 'cm', group: 'Movilidad', color: '#4ba283', icon: '↔', cadence: 'daily', decimals: 1 },
  { id: 'walking_asymmetry_percentage', label: 'Asimetría al caminar', short: 'Asimetría', unit: '%', group: 'Movilidad', color: '#b47745', icon: '≠', cadence: 'daily', decimals: 1 },
  { id: 'walking_double_support_percentage', label: 'Doble apoyo al caminar', short: 'Doble apoyo', unit: '%', group: 'Movilidad', color: '#9b7654', icon: 'Ⅱ', cadence: 'daily', decimals: 1 },
  { id: 'stair_speed_up', label: 'Velocidad subiendo escaleras', short: 'Escaleras subida', unit: 'm/s', group: 'Movilidad', color: '#8b7a43', icon: '↥', cadence: 'daily', decimals: 2 },
  { id: 'stair_speed_down', label: 'Velocidad bajando escaleras', short: 'Escaleras bajada', unit: 'm/s', group: 'Movilidad', color: '#a28451', icon: '↧', cadence: 'daily', decimals: 2 },

  { id: 'time_in_daylight', label: 'Tiempo con luz diurna', short: 'Luz diurna', unit: 'min', group: 'Bienestar', color: '#e59d2f', icon: '☀', cadence: 'daily', decimals: 0, completeDaysOnly: true },
  { id: 'physical_effort', label: 'Esfuerzo físico', short: 'Esfuerzo', unit: 'kcal/h·kg', group: 'Bienestar', color: '#d65f52', icon: '◆', cadence: 'daily', decimals: 2 },
  { id: 'basal_energy_burned', label: 'Energía en reposo', short: 'Energía reposo', unit: 'kcal', group: 'Bienestar', color: '#7f87a8', icon: '◐', cadence: 'daily', decimals: 0, completeDaysOnly: true },
]

const METRIC_BY_ID = Object.fromEntries(METRICS.map((metric) => [metric.id, metric]))
const GROUPS = ['Actividad', 'Corazón', 'Respiración', 'Sueño', 'Movilidad', 'Bienestar']
const PRIMARY_IDS = ['step_count', 'active_energy', 'sleep_analysis', 'resting_heart_rate', 'heart_rate_variability', 'vo2_max']
const RANGES = [
  { value: 30, label: '30 días' },
  { value: 90, label: '90 días' },
  { value: 365, label: '1 año' },
  { value: 3650, label: 'Todo' },
]

const SLEEP_STAGES = [
  {
    key: 'rem',
    label: 'REM',
    color: '#8b5cf6',
    summary: 'Fase asociada a sueños vívidos y procesamiento de memoria y emociones.',
    detection: 'Apple la estima con modelos que analizan patrones del acelerómetro y del sensor de frecuencia cardiaca. No mide directamente la actividad cerebral.',
  },
  {
    key: 'core',
    label: 'Esencial',
    color: '#3b82f6',
    summary: 'Sueño generalmente más ligero que ocupa buena parte de la noche.',
    detection: 'El Apple Watch la diferencia de REM, profundo y vigilia combinando movimiento y patrones cardiacos mediante algoritmos de clasificación.',
  },
  {
    key: 'deep',
    label: 'Profundo',
    color: '#2446a8',
    summary: 'Fase de sueño de ondas lentas vinculada a recuperación física.',
    detection: 'Apple la estima a partir de señales de movimiento y frecuencia cardiaca. Es una clasificación algorítmica, no una polisomnografía.',
  },
  {
    key: 'awake',
    label: 'Despierto',
    color: '#f59e0b',
    summary: 'Periodos de vigilia detectados durante la ventana de sueño.',
    detection: 'El reloj infiere despertares, incluidos algunos muy breves, por cambios de movimiento y señales cardiacas; puede no coincidir con tu recuerdo.',
  },
]

const NOTES = {
  step_count: ['Resume tu actividad cotidiana consolidada por Apple Salud.', 'Conviene interpretarlo respecto a tu rutina; un día aislado no define tu estado físico.', 'Observa tendencias semanales y cambios sostenidos, incluyendo descanso, viajes o enfermedad.'],
  active_energy: ['Estima la energía asociada al movimiento y al ejercicio.', 'Depende de tus datos personales y de la calibración; no equivale exactamente al gasto real.', 'Úsala junto con pasos, ejercicio y distancia, no como objetivo aislado.'],
  walking_running_distance: ['Estima la distancia acumulada andando y corriendo.', 'Está relacionada con los pasos, la longitud de zancada y los entrenamientos registrados.', 'Compara periodos similares y revisa la calibración si detectas cambios improbables.'],
  apple_exercise_time: ['Cuenta minutos que alcanzan la intensidad considerada ejercicio por Apple.', 'Puede variar según tu capacidad aeróbica y el tipo de actividad.', 'Complementa el dato con el tipo de entrenamiento y cómo te sentiste.'],
  apple_stand_hour: ['Cuenta las horas en las que te levantaste y te moviste al menos un minuto.', 'Mide distribución del movimiento, no intensidad ni forma física.', 'Puede servir para detectar jornadas muy sedentarias.'],
  apple_stand_time: ['Suma los minutos registrados de pie.', 'No sustituye a la actividad física y puede depender del uso del reloj.', 'Interprétalo junto con horas de pie y tiempo de ejercicio.'],
  flights_climbed: ['Estima los desniveles equivalentes a pisos subidos.', 'Puede variar por escaleras, cuestas y precisión del sensor barométrico.', 'Es más útil como tendencia que como cifra exacta diaria.'],
  resting_heart_rate: ['Estima tu frecuencia cardiaca cuando estás en reposo.', 'Cambios persistentes pueden relacionarse con entrenamiento, recuperación, estrés o enfermedad, pero no son diagnósticos.', 'Revisa tendencias de varios días y consulta si hay síntomas o cambios preocupantes.'],
  heart_rate_variability: ['Mide la variación temporal entre latidos en milisegundos.', 'Es muy personal y puede cambiar con sueño, carga, alcohol, estrés o enfermedad.', 'Compárala solo con tu propio nivel habitual y evita conclusiones por una medición.'],
  vo2_max: ['Es una estimación de capacidad aeróbica obtenida en actividades compatibles.', 'Se registra de forma esporádica; por eso se analiza en ventanas de 90 días.', 'Busca cambios sostenidos y considera el tipo y frecuencia de tus entrenamientos.'],
  cardio_recovery: ['Estima cuánto desciende la frecuencia cardiaca tras finalizar un ejercicio.', 'Depende del esfuerzo, la recuperación activa y la calidad de la medición.', 'Compara entrenamientos similares, no sesiones de distinta intensidad.'],
  walking_heart_rate_average: ['Resume la frecuencia cardiaca mientras caminas.', 'La velocidad, pendientes, temperatura y fatiga influyen en el valor.', 'Interprétala junto con velocidad al caminar y frecuencia en reposo.'],
  heart_rate: ['Muestra la media diaria y conserva el mínimo y máximo registrados.', 'La media mezcla reposo, actividad y ejercicio; no debe interpretarse de forma aislada.', 'Usa el rango diario como contexto y las métricas específicas para analizar tendencias.'],
  respiratory_rate: ['Estima cuántas respiraciones realizas por minuto, principalmente durante el sueño.', 'Lo más útil es detectar desviaciones sostenidas respecto a tu rango personal.', 'Si el cambio persiste o aparece con síntomas respiratorios, consulta a un profesional.'],
  blood_oxygen_saturation: ['Estima el porcentaje de oxígeno transportado en la sangre.', 'Las lecturas de muñeca pueden verse afectadas por movimiento, ajuste, frío y perfusión.', 'No utilices el reloj para diagnosticar; ante valores preocupantes o síntomas, busca valoración sanitaria.'],
  sleep_analysis: ['Resume duración, despertares y fases estimadas del sueño.', 'Las fases son estimaciones y una noche aislada puede ser atípica.', 'Prioriza regularidad, duración y tendencias de varias semanas.'],
  walking_speed: ['Estima tu velocidad habitual al caminar con el iPhone.', 'Depende del terreno, calzado, cansancio y de cómo llevas el teléfono.', 'Compárala en periodos largos y junto con el resto de métricas de movilidad.'],
  walking_step_length: ['Estima la distancia media cubierta en cada paso.', 'Está influida por altura, velocidad, terreno y forma de llevar el iPhone.', 'Observa cambios sostenidos, no pequeñas variaciones diarias.'],
  walking_asymmetry_percentage: ['Estima la proporción de pasos cuya sincronización difiere entre ambos lados.', 'Los días con pocas muestras pueden producir valores extremos.', 'Analízala con mediana y cobertura; si cambia persistentemente con dolor o limitación, consulta.'],
  walking_double_support_percentage: ['Estima el porcentaje de la marcha con ambos pies apoyados.', 'Cambia con velocidad, terreno y estabilidad; no tiene un significado aislado universal.', 'Interprétalo junto con velocidad, longitud del paso y asimetría.'],
  stair_speed_up: ['Estima la velocidad al subir escaleras.', 'Depende del número de tramos, pausas y disponibilidad de muestras.', 'Usa tendencias de 30 o 90 días para reducir el ruido.'],
  stair_speed_down: ['Estima la velocidad al bajar escaleras.', 'Puede variar por seguridad, terreno, fatiga y número de muestras.', 'Busca cambios persistentes y compáralos con otras métricas de movilidad.'],
  time_in_daylight: ['Estima los minutos que pasas expuesto a luz diurna.', 'Puede faltar cuando no llevas un dispositivo compatible.', 'Úsalo como contexto de hábitos, sueño y tiempo al aire libre.'],
  physical_effort: ['Estima la intensidad relativa del esfuerzo físico.', 'Es una métrica derivada y depende del tipo de actividad y tus datos personales.', 'Resulta más útil junto con ejercicio, frecuencia cardiaca y recuperación.'],
  basal_energy_burned: ['Estima la energía utilizada por tu organismo en reposo.', 'No mide directamente tu metabolismo y depende de edad, sexo, altura y peso configurados.', 'Úsala como contexto del gasto total, no para inferir cambios de grasa o dieta.'],
}

const METRIC_GUIDE = {
  step_count: {
    summary: 'Cuantifica tu movimiento cotidiano y ayuda a comparar de forma sencilla cuánto te has desplazado entre días y semanas.',
    apple: 'El iPhone y el Apple Watch detectan pasos mediante sus sensores de movimiento. Apple Salud ordena las fuentes y consolida las aportaciones para evitar, en lo posible, contar dos veces periodos coincidentes.',
  },
  active_energy: {
    summary: 'Estima las kilocalorías gastadas mediante movimiento y ejercicio por encima de la energía que el cuerpo emplea en reposo.',
    apple: 'Apple combina movimiento, frecuencia cardiaca durante actividades compatibles y los datos físicos del perfil —como edad, sexo, altura y peso— mediante algoritmos propios.',
  },
  walking_running_distance: {
    summary: 'Resume la distancia diaria recorrida andando o corriendo y permite contextualizar los pasos y el nivel de actividad.',
    apple: 'Se estima con GPS cuando está disponible y con sensores de movimiento, ritmo y longitud de paso. La calibración del reloj y del iPhone influye en el resultado.',
  },
  apple_exercise_time: {
    summary: 'Cuenta los minutos de actividad cuya intensidad alcanza el nivel que Apple considera ejercicio para ti.',
    apple: 'El reloj evalúa intensidad, movimiento y frecuencia cardiaca; los criterios pueden variar según la actividad y tu nivel cardiovascular estimado.',
  },
  apple_stand_hour: {
    summary: 'Indica en cuántas horas del día te levantaste y te moviste durante al menos un minuto.',
    apple: 'El Apple Watch usa sus sensores de movimiento para identificar una breve actividad de pie dentro de cada hora. No representa horas completas permaneciendo de pie.',
  },
  apple_stand_time: {
    summary: 'Suma los minutos en los que el reloj detectó que estabas de pie y aporta contexto sobre el sedentarismo diario.',
    apple: 'Se deriva de la orientación y el movimiento detectados por el Apple Watch. Puede depender de cómo lleves el reloj y del tipo de actividad.',
  },
  flights_climbed: {
    summary: 'Expresa el desnivel ascendente como un número aproximado de pisos y complementa pasos y distancia.',
    apple: 'El iPhone o Apple Watch combinan cambios de altitud del barómetro con movimiento. Cuestas, presión atmosférica y tramos cortos pueden afectar la estimación.',
  },
  resting_heart_rate: {
    summary: 'Estima los latidos por minuto cuando estás en reposo y resulta útil para observar recuperación y cambios respecto a tu nivel habitual.',
    apple: 'El sensor óptico mide el pulso periódicamente. Apple selecciona lecturas de baja actividad y aplica su algoritmo para obtener una estimación diaria de reposo.',
  },
  heart_rate_variability: {
    summary: 'Mide en milisegundos cómo varía el intervalo entre latidos; es una señal muy personal relacionada con la regulación del organismo.',
    apple: 'El Apple Watch obtiene intervalos entre latidos con el sensor cardiaco y Salud registra la VFC como SDNN en mediciones puntuales, no como una lectura continua.',
  },
  vo2_max: {
    summary: 'Estima la capacidad máxima del cuerpo para utilizar oxígeno durante el ejercicio y permite seguir la evolución de la forma aeróbica.',
    apple: 'Apple estima la capacidad aeróbica con frecuencia cardiaca, movimiento, ritmo, desnivel y datos personales durante caminatas, carreras o senderismo compatibles; no es una prueba directa de laboratorio.',
  },
  cardio_recovery: {
    summary: 'Mide cuánto disminuye la frecuencia cardiaca después de terminar un ejercicio y aporta contexto sobre la recuperación cardiovascular.',
    apple: 'Se calcula comparando el pulso del final del entrenamiento con lecturas posteriores, especialmente alrededor del primer minuto. El enfriamiento activo puede modificarlo.',
  },
  walking_heart_rate_average: {
    summary: 'Muestra el pulso medio mientras caminas y ayuda a contextualizar el esfuerzo que supone una actividad cotidiana.',
    apple: 'El Apple Watch relaciona lecturas del sensor óptico con periodos detectados de marcha y calcula una media. Velocidad, pendiente, temperatura y ajuste del reloj influyen.',
  },
  heart_rate: {
    summary: 'Resume el pulso observado durante el día y muestra su media junto con los valores mínimo y máximo registrados.',
    apple: 'El sensor óptico realiza lecturas periódicas y aumenta su frecuencia durante entrenamientos. No es un registro continuo con la misma cadencia durante todo el día.',
  },
  respiratory_rate: {
    summary: 'Estima cuántas respiraciones realizas por minuto durante el sueño y facilita detectar cambios respecto a tu patrón personal.',
    apple: 'Mientras duermes con el reloj, Apple analiza movimientos sutiles de la muñeca asociados a la respiración. La medición está orientada a tendencias y no a diagnóstico.',
  },
  blood_oxygen_saturation: {
    summary: 'Estima el porcentaje de hemoglobina que transporta oxígeno y ofrece contexto adicional sobre tu estado respiratorio general.',
    apple: 'En modelos compatibles, LEDs y fotodiodos iluminan la muñeca y analizan la luz reflejada. Movimiento, frío, perfusión, tatuajes y ajuste pueden afectar la lectura.',
  },
  sleep_analysis: {
    summary: 'Muestra cuánto dormiste y cómo se repartió el tiempo entre REM, sueño esencial, profundo y periodos despierto.',
    apple: 'Apple usa datos del acelerómetro y del sensor de frecuencia cardiaca para clasificar las fases. Son estimaciones algorítmicas y no equivalen a medir ondas cerebrales en una polisomnografía.',
  },
  walking_speed: {
    summary: 'Estima tu velocidad habitual al caminar y puede ayudar a observar cambios sostenidos en movilidad y ritmo cotidiano.',
    apple: 'El iPhone utiliza sus sensores cuando lo llevas en el bolsillo o cerca de la cintura. El terreno, la ubicación del teléfono y el tipo de trayecto afectan la estimación.',
  },
  walking_step_length: {
    summary: 'Estima la distancia media que avanzas en cada paso y aporta contexto sobre la mecánica y el ritmo de la marcha.',
    apple: 'El iPhone combina patrones de movimiento con sus algoritmos personalizados mientras caminas llevándolo cerca de la cintura.',
  },
  walking_asymmetry_percentage: {
    summary: 'Estima el porcentaje de pasos en los que la sincronización entre ambos lados de la marcha es desigual.',
    apple: 'El iPhone analiza patrones de movimiento al caminar cuando lo llevas en el bolsillo o cerca de la cintura. Es una estimación indirecta, no un análisis clínico de la marcha.',
  },
  walking_double_support_percentage: {
    summary: 'Estima qué porcentaje de cada ciclo de marcha mantienes ambos pies apoyados simultáneamente.',
    apple: 'El iPhone infiere las fases del paso mediante sus sensores de movimiento y algoritmos de movilidad. La velocidad y el terreno cambian naturalmente el resultado.',
  },
  stair_speed_up: {
    summary: 'Estima la velocidad con la que subes escaleras y permite observar tendencias funcionales a lo largo del tiempo.',
    apple: 'El dispositivo combina movimiento y cambios de altitud en tramos identificados como escaleras. Las pausas y el reducido número de muestras pueden introducir ruido.',
  },
  stair_speed_down: {
    summary: 'Estima la velocidad con la que bajas escaleras, una actividad relacionada con movilidad, equilibrio y confianza.',
    apple: 'El dispositivo combina movimiento y cambios de altitud en tramos identificados como escaleras. La forma de llevar el iPhone y las pausas influyen.',
  },
  time_in_daylight: {
    summary: 'Estima los minutos de exposición a luz diurna y ayuda a contextualizar hábitos al aire libre y regularidad del sueño.',
    apple: 'En relojes compatibles, el sensor de luz ambiental estima el tiempo bajo condiciones de luz diurna. Solo puede medirlo mientras llevas puesto el dispositivo.',
  },
  physical_effort: {
    summary: 'Expresa la intensidad del esfuerzo físico en relación con tu peso y permite comparar la carga de actividades diferentes.',
    apple: 'Es una métrica derivada por Apple a partir de actividad, movimiento, frecuencia cardiaca y datos personales cuando están disponibles. Su algoritmo completo no es público.',
  },
  basal_energy_burned: {
    summary: 'Estima las kilocalorías que tu organismo utiliza para mantener funciones básicas incluso sin realizar actividad.',
    apple: 'Apple la calcula principalmente a partir de edad, sexo, altura y peso configurados en Salud. Es un modelo estimado, no una medición directa del metabolismo.',
  },
}

async function api(path, options) {
  const response = await fetch(path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (response.status === 401) throw new Error('AUTH')
  if (response.status === 429) throw new Error('RATE_LIMIT')
  if (!response.ok) throw new Error('API')
  return response.json()
}

function parseDay(value) {
  return new Date(`${value}T12:00:00`)
}

function dayKey(date = new Date()) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function shiftDays(date, amount) {
  const result = new Date(date)
  result.setDate(result.getDate() + amount)
  return result
}

function average(values) {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null
}

function formatValue(metric, value) {
  if (value == null || Number.isNaN(value)) return '—'
  if (metric.id === 'step_count') return Math.trunc(value).toLocaleString('es-ES')
  return value.toLocaleString('es-ES', {
    minimumFractionDigits: 0,
    maximumFractionDigits: metric.decimals,
  })
}

function filterByDays(data, days) {
  if (!data.length || days >= 3650) return data
  const latest = parseDay(data.at(-1).date)
  const cutoff = shiftDays(latest, -(days - 1))
  return data.filter((point) => parseDay(point.date) >= cutoff)
}

function dataForTrend(metric, data) {
  if (!metric.completeDaysOnly || !data.length) return data
  const today = dayKey()
  return data.filter((point) => point.date !== today)
}

function valuesInWindow(data, latest, startDaysAgo, endDaysAgo) {
  const start = shiftDays(latest, -startDaysAgo)
  const end = shiftDays(latest, -endDaysAgo)
  return data
    .filter((point) => {
      const date = parseDay(point.date)
      return date >= start && date <= end && Number.isFinite(point.value)
    })
    .map((point) => point.value)
}

function trendFor(metric, input) {
  const data = dataForTrend(metric, input || []).filter((point) => Number.isFinite(point.value))
  if (!data.length) return { direction: 'neutral', change: null, mode: metric.cadence }
  const latest = parseDay(data.at(-1).date)
  let currentValues
  let baselineValues
  let currentLabel
  let baselineLabel
  let enough

  if (metric.cadence === 'sparse') {
    currentValues = valuesInWindow(data, latest, 89, 0)
    baselineValues = valuesInWindow(data, latest, 269, 90)
    currentLabel = 'últimos 90 días'
    baselineLabel = '180 días anteriores'
    enough = currentValues.length >= 2 && baselineValues.length >= 2
  } else {
    currentValues = valuesInWindow(data, latest, 6, 0)
    baselineValues = valuesInWindow(data, latest, 34, 7)
    currentLabel = 'últimos 7 días'
    baselineLabel = '28 días anteriores'
    enough = currentValues.length >= 4 && baselineValues.length >= 14
  }

  if (!enough) {
    return {
      direction: 'neutral',
      change: null,
      mode: metric.cadence,
      currentCount: currentValues.length,
      baselineCount: baselineValues.length,
      currentLabel,
      baselineLabel,
    }
  }

  const current = average(currentValues)
  const baseline = average(baselineValues)
  if (baseline == null || baseline === 0) return { direction: 'neutral', change: null, mode: metric.cadence }
  const change = ((current - baseline) / Math.abs(baseline)) * 100
  return {
    direction: Math.abs(change) < 3 ? 'neutral' : change > 0 ? 'up' : 'down',
    change,
    current,
    baseline,
    currentCount: currentValues.length,
    baselineCount: baselineValues.length,
    currentLabel,
    baselineLabel,
    mode: metric.cadence,
  }
}

function trendText(trend) {
  if (trend.change == null) {
    return trend.mode === 'sparse'
      ? `Todavía faltan mediciones para comparar ${trend.currentLabel || 'el periodo reciente'} con una referencia anterior.`
      : 'Aún no hay cobertura suficiente en ambos periodos para calcular una comparación fiable.'
  }
  return `La media de los ${trend.currentLabel} está un ${Math.abs(trend.change).toFixed(1)} % ${trend.change >= 0 ? 'por encima' : 'por debajo'} de los ${trend.baselineLabel}.`
}

function coverageFor(metric, data, days) {
  if (!data.length) return 'Sin datos'
  if (metric.cadence === 'sparse') return `${data.length} mediciones`
  const first = parseDay(data[0].date)
  const last = parseDay(data.at(-1).date)
  const span = Math.max(1, Math.round((last - first) / 86400000) + 1)
  const expected = days >= 3650 ? span : Math.min(days, span)
  const visible = filterByDays(data, days).length
  return `${Math.round((visible / expected) * 100)} % de cobertura`
}

function Login({ onSuccess }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ password }) })
      onSuccess()
    } catch (failure) {
      if (failure.message === 'RATE_LIMIT') setError('Demasiados intentos. Espera cinco minutos o reinicia solo el dashboard.')
      else if (failure.message === 'AUTH') setError('Contraseña incorrecta.')
      else setError('El servidor no pudo procesar el acceso.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card">
        <div className="brand-mark">H</div>
        <p className="eyebrow">HealthScope privado</p>
        <h1>Tu salud, en perspectiva.</h1>
        <p className="muted">Accede al dashboard almacenado en tu Raspberry Pi.</p>
        <form onSubmit={submit}>
          <label htmlFor="password">Contraseña</label>
          <input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} autoFocus />
          {error && <p className="form-error">{error}</p>}
          <button className="primary-button" type="submit" disabled={loading || password.length < 1}>{loading ? 'Accediendo…' : 'Entrar'}</button>
        </form>
        <p className="privacy-note">Los datos permanecen en tu red privada.</p>
      </section>
    </main>
  )
}

function Sidebar({ collapsed, onToggle, selected, onSelect, mobileOpen, closeMobile }) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-header">
        <div className="brand-mark small">H</div>
        {!collapsed && <strong>HealthScope</strong>}
        <button className="icon-button collapse-button" onClick={onToggle} aria-label="Plegar menú">{collapsed ? '›' : '‹'}</button>
      </div>
      <nav>
        <button className="nav-overview active"><span>⌂</span>{!collapsed && 'Resumen'}</button>
        {GROUPS.map((group) => (
          <div className="nav-group" key={group}>
            {!collapsed && <p>{group}</p>}
            {METRICS.filter((metric) => metric.group === group).map((metric) => (
              <button key={metric.id} className={selected === metric.id ? 'selected' : ''} onClick={() => { onSelect(metric.id); closeMobile() }} title={metric.label}>
                <span className="nav-icon" style={{ color: metric.color }}>{metric.icon}</span>
                {!collapsed && metric.short}
              </button>
            ))}
          </div>
        ))}
      </nav>
      {!collapsed && <div className="sidebar-footer"><span className="status-dot" /> Raspberry Pi conectada</div>}
    </aside>
  )
}

function MetricCard({ metric, data, days, selected, onClick }) {
  const latest = data?.at(-1)?.value
  const trend = trendFor(metric, data || [])
  return (
    <button className={`metric-card ${selected ? 'selected' : ''}`} onClick={onClick} style={{ '--accent': metric.color }}>
      <div className="metric-card-top">
        <span className="metric-icon">{metric.icon}</span>
        <span className={`trend-pill ${trend.direction}`}>{trend.change == null ? 'Sin comparación' : `${trend.change > 0 ? '+' : ''}${trend.change.toFixed(1)} %`}</span>
      </div>
      <p>{metric.short}</p>
      <strong>{formatValue(metric, latest)}</strong>
      <span>{metric.unit} · {coverageFor(metric, data || [], days)}</span>
    </button>
  )
}

function PatternCard({ metric, data, onMore }) {
  const trend = trendFor(metric, data)
  const title = trend.change == null
    ? 'Cobertura insuficiente para comparar'
    : trend.direction === 'neutral'
      ? 'En línea con tu referencia'
      : trend.direction === 'up'
        ? 'Por encima de tu referencia'
        : 'Por debajo de tu referencia'
  return (
    <article className="pattern-card">
      <div className={`pattern-symbol ${trend.direction}`}>{trend.direction === 'up' ? '↗' : trend.direction === 'down' ? '↘' : '→'}</div>
      <div>
        <p className="eyebrow">Comparación personal</p>
        <h3>{title}</h3>
        <p>{trendText(trend)}</p>
        <button className="text-button" onClick={onMore}>Más información →</button>
      </div>
    </article>
  )
}

function MetricHighlights({ metric, point }) {
  const details = point?.details
  if (!details) return null
  if (metric.id === 'heart_rate') {
    return (
      <div className="highlight-row">
        <div><span>Mínima</span><strong>{formatValue(metric, details.minimum)}</strong><small>lpm</small></div>
        <div><span>Media</span><strong>{formatValue(metric, point.value)}</strong><small>lpm</small></div>
        <div><span>Máxima</span><strong>{formatValue(metric, details.maximum)}</strong><small>lpm</small></div>
      </div>
    )
  }
  if (metric.id === 'sleep_analysis') {
    return (
      <div className="highlight-row sleep-stages">
        {SLEEP_STAGES.map((stage) => {
          const tooltipId = `sleep-stage-${stage.key}`
          return (
            <div className="sleep-stage-card" key={stage.key} style={{ '--stage-color': stage.color }}>
              <div className="stage-heading">
                <span>{stage.label}</span>
                <button className="stage-help" type="button" aria-label={`Cómo estima Apple la fase ${stage.label}`} aria-describedby={tooltipId}>i</button>
                <span className="stage-tooltip" id={tooltipId} role="tooltip">{stage.detection}</span>
              </div>
              <strong>{formatValue(metric, details[stage.key])}</strong><small>h</small>
              <p>{stage.summary}</p>
            </div>
          )
        })}
      </div>
    )
  }
  return null
}

function MoreInfo({ metric, data, days, onBack }) {
  const trend = trendFor(metric, data)
  const notes = NOTES[metric.id] || ['Métrica procedente de Apple Salud.', 'Interprétala respecto a tu contexto personal.', 'Observa tendencias sostenidas y la cobertura disponible.']
  const guide = METRIC_GUIDE[metric.id] || { summary: notes[0], apple: 'Apple Salud recibe esta métrica desde dispositivos y aplicaciones autorizados. El método concreto depende de la fuente.' }
  const healthScopeMethod = metric.id === 'heart_rate'
    ? 'Health Auto Export entrega el resumen diario. HealthScope conserva la versión más reciente de cada fecha y presenta media, mínimo y máximo sin reinterpretar las lecturas originales.'
    : metric.id === 'sleep_analysis'
      ? 'Health Auto Export entrega el total diario y las fases estimadas. HealthScope conserva la versión más reciente de cada fecha. El total puede incluir intervalos “dormido” que Apple no asignó a una fase concreta.'
      : 'Health Auto Export entrega un resumen diario consolidado por Apple Salud. HealthScope conserva la versión más reciente recibida para cada fecha y no combina de nuevo fuentes o dispositivos.'
  return (
    <main className="detail-page">
      <button className="back-button" onClick={onBack}>← Volver al dashboard</button>
      <p className="eyebrow">Más información</p>
      <h1>{metric.label}</h1>
      <p className="detail-lead">{guide.summary}</p>
      <div className="detail-grid">
        <section><h2>Qué es y para qué sirve</h2><p>{notes[0]}</p></section>
        <section><h2>Cómo lo obtiene Apple</h2><p>{guide.apple}</p><p className="method-note">Apple puede actualizar sus algoritmos y no publica todos los detalles internos de cada estimación.</p></section>
        <section><h2>Cómo se presenta en HealthScope</h2><p>{healthScopeMethod}</p></section>
        <section><h2>Cómo interpretarlo</h2><p>{notes[1]}</p></section>
        <section><h2>Qué hemos observado</h2><p>{trendText(trend)}</p><p className="coverage-detail">{coverageFor(metric, data, days)} · {data.length} registros cargados para el análisis.</p></section>
        <section><h2>Comparación utilizada</h2><p>{metric.cadence === 'sparse' ? 'HealthScope compara la media de las mediciones de los últimos 90 días con los 180 días anteriores. Se requieren al menos dos mediciones en cada periodo.' : 'HealthScope compara la media de los últimos 7 días con los 28 días anteriores. En métricas acumulativas excluye el día actual mientras está incompleto.'}</p></section>
        <section><h2>Limitaciones y siguiente paso</h2><p>{notes[2]}</p><p>Apple Salud y Health Auto Export pueden revisar valores retrospectivamente; confirma cambios aislados en contexto.</p></section>
      </div>
      <div className="medical-note">HealthScope ayuda a explorar tendencias personales; no diagnostica enfermedades ni sustituye asesoramiento médico. Si tienes síntomas o un dato te preocupa, consulta a un profesional sanitario.</div>
    </main>
  )
}

async function loadMetricBatches(days, cancelled) {
  const results = {}
  for (let index = 0; index < METRICS.length; index += 5) {
    const batch = METRICS.slice(index, index + 5)
    const values = await Promise.all(batch.map((metric) => api(`/api/metrics/${metric.id}?days=${days}`).catch(() => ({ data: [] }))))
    if (cancelled()) return null
    batch.forEach((metric, itemIndex) => { results[metric.id] = values[itemIndex].data || [] })
  }
  return results
}

function Dashboard({ onLogout }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [dark, setDark] = useState(() => localStorage.getItem('healthscope-theme') === 'dark')
  const [selected, setSelected] = useState('step_count')
  const [days, setDays] = useState(90)
  const [series, setSeries] = useState({})
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [detail, setDetail] = useState(false)

  const selectedMetric = METRIC_BY_ID[selected]
  const selectedData = useMemo(() => series[selected] || [], [series, selected])
  const chartData = useMemo(() => filterByDays(selectedData, days).map((point) => ({
    ...point,
    display: point.value,
    minimum: point.details?.minimum,
    maximum: point.details?.maximum,
    rem: point.details?.rem,
    core: point.details?.core,
    deep: point.details?.deep,
    awake: point.details?.awake,
  })), [selectedData, days])
  const latestPoint = chartData.at(-1)

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    localStorage.setItem('healthscope-theme', dark ? 'dark' : 'light')
  }, [dark])

  useEffect(() => {
    let isCancelled = false
    setLoading(true)
    setError('')
    const requestedDays = days >= 3650 ? 3650 : Math.max(days, 365)
    Promise.all([
      api('/api/status'),
      loadMetricBatches(requestedDays, () => isCancelled),
    ]).then(([statusResult, metricResults]) => {
      if (isCancelled || !metricResults) return
      setStatus(statusResult)
      setSeries(metricResults)
    }).catch((failure) => {
      if (failure.message === 'AUTH') onLogout()
      else setError('No se pudieron cargar los datos. Comprueba el servicio de ingestión.')
    }).finally(() => { if (!isCancelled) setLoading(false) })
    return () => { isCancelled = true }
  }, [days, onLogout])

  if (detail) return <MoreInfo metric={selectedMetric} data={selectedData} days={days} onBack={() => setDetail(false)} />

  const primaryMetrics = PRIMARY_IDS.map((id) => METRIC_BY_ID[id])
  const secondaryMetrics = METRICS.filter((metric) => !PRIMARY_IDS.includes(metric.id))

  return (
    <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} selected={selected} onSelect={(id) => { setSelected(id); setDetail(false) }} mobileOpen={mobileOpen} closeMobile={() => setMobileOpen(false)} />
      {mobileOpen && <button className="mobile-overlay" aria-label="Cerrar menú" onClick={() => setMobileOpen(false)} />}
      <div className="content-shell">
        <header>
          <button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)}>☰</button>
          <div><p className="eyebrow">Dashboard privado</p><h1>Resumen de salud</h1></div>
          <div className="header-actions">
            <div className="sync-status"><span className="status-dot" /><span>Última recepción<br /><strong>{status?.last_import_at ? new Date(status.last_import_at).toLocaleString('es-ES') : 'Sin datos'}</strong></span></div>
            <button className="theme-toggle" onClick={() => setDark((value) => !value)} aria-label="Cambiar tema">{dark ? '☀' : '☾'}</button>
            <button className="logout-button" onClick={onLogout}>Salir</button>
          </div>
        </header>
        <main className="dashboard-main">
          <section className="intro-row">
            <div><h2>Tu referencia personal</h2><p>25 métricas consolidadas de Apple Salud · histórico privado y actualizado.</p></div>
            <div className="range-selector">{RANGES.map((range) => <button key={range.value} className={days === range.value ? 'active' : ''} onClick={() => setDays(range.value)}>{range.label}</button>)}</div>
          </section>
          {error && <div className="error-banner">{error}</div>}
          <section className="metric-grid">{primaryMetrics.map((metric) => <MetricCard key={metric.id} metric={metric} data={series[metric.id] || []} days={days} selected={selected === metric.id} onClick={() => setSelected(metric.id)} />)}</section>
          <section className="analytics-grid">
            <article className="chart-card">
              <div className="card-heading"><div><p className="eyebrow">Evolución</p><h2>{selectedMetric.label}</h2></div><div className="chart-current"><strong>{formatValue(selectedMetric, latestPoint?.value)}</strong><span>{selectedMetric.unit} · último registro</span></div></div>
              <div className="metric-context"><strong>Qué te muestra</strong><p>{METRIC_GUIDE[selectedMetric.id]?.summary || NOTES[selectedMetric.id]?.[0]}</p></div>
              <MetricHighlights metric={selectedMetric} point={latestPoint} />
              <div className="chart-area">{loading ? <div className="skeleton" /> : chartData.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 12, right: 8, left: -8, bottom: 0 }}><defs><linearGradient id="metricFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={selectedMetric.color} stopOpacity={0.28} /><stop offset="100%" stopColor={selectedMetric.color} stopOpacity={0.02} /></linearGradient></defs><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--grid)" /><XAxis dataKey="date" tickFormatter={(value) => value.slice(5)} tick={{ fill: 'var(--muted)', fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={28} /><YAxis tick={{ fill: 'var(--muted)', fontSize: 11 }} axisLine={false} tickLine={false} width={58} /><Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 14, boxShadow: 'var(--shadow)' }} formatter={(value, name) => [`${formatValue(selectedMetric, value)} ${selectedMetric.unit}`, name]} labelFormatter={(value) => parseDay(value).toLocaleDateString('es-ES', { dateStyle: 'long' })} /><Area type="monotone" dataKey="display" name={selectedMetric.id === 'sleep_analysis' ? 'Sueño total' : selectedMetric.id === 'heart_rate' ? 'Media' : selectedMetric.label} stroke={selectedMetric.color} strokeWidth={2.5} fill="url(#metricFill)" activeDot={{ r: 5 }} />{selectedMetric.id === 'heart_rate' && <Line type="monotone" dataKey="minimum" name="Mínima" stroke="#5f9eea" dot={false} strokeDasharray="4 4" />}{selectedMetric.id === 'heart_rate' && <Line type="monotone" dataKey="maximum" name="Máxima" stroke="#ef6b75" dot={false} strokeDasharray="4 4" />}{selectedMetric.id === 'sleep_analysis' && SLEEP_STAGES.map((stage) => <Line key={stage.key} type="monotone" dataKey={stage.key} name={stage.label} stroke={stage.color} strokeWidth={2} dot={false} connectNulls />)}</AreaChart></ResponsiveContainer> : <div className="empty-state">No hay datos para este periodo.</div>}</div>
            </article>
            <PatternCard metric={selectedMetric} data={selectedData} onMore={() => setDetail(true)} />
          </section>
          <section className="secondary-section"><div><p className="eyebrow">Explorar</p><h2>Más métricas</h2><p>Selecciona una tarjeta para analizar su evolución, cobertura y contexto.</p></div><div className="compact-metrics">{secondaryMetrics.map((metric) => <MetricCard key={metric.id} metric={metric} data={series[metric.id] || []} days={days} selected={selected === metric.id} onClick={() => setSelected(metric.id)} />)}</div></section>
        </main>
      </div>
    </div>
  )
}

function App() {
  const [authenticated, setAuthenticated] = useState(null)
  useEffect(() => { api('/api/auth/status').then((result) => setAuthenticated(result.authenticated)).catch(() => setAuthenticated(false)) }, [])
  async function logout() { try { await api('/api/auth/logout', { method: 'POST' }) } finally { setAuthenticated(false) } }
  if (authenticated == null) return <div className="boot-screen"><div className="brand-mark">H</div></div>
  return authenticated ? <Dashboard onLogout={logout} /> : <Login onSuccess={() => setAuthenticated(true)} />
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
