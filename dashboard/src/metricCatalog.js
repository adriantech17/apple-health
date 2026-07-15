export const METRICS = [
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

export const METRIC_BY_ID = Object.fromEntries(METRICS.map((metric) => [metric.id, metric]))
export const GROUPS = ['Actividad', 'Corazón', 'Respiración', 'Sueño', 'Movilidad', 'Bienestar']
export const PRIMARY_IDS = ['step_count', 'active_energy', 'sleep_analysis', 'resting_heart_rate', 'heart_rate_variability', 'vo2_max']
export const RANGES = [
  { value: 30, label: '30 días' },
  { value: 90, label: '90 días' },
  { value: 365, label: '1 año' },
  { value: 3650, label: 'Todo' },
]

export const SLEEP_STAGES = [
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

export const NOTES = {
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
export const METRIC_GUIDE = {
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
