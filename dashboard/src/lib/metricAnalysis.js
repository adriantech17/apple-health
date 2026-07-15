export function parseDay(value) {
  return new Date(`${value}T12:00:00`)
}
export function dayKey(date = new Date()) {
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

export function formatValue(metric, value) {
  if (value == null || Number.isNaN(value)) return '—'
  if (metric.id === 'step_count') return Math.trunc(value).toLocaleString('es-ES')
  return value.toLocaleString('es-ES', {
    minimumFractionDigits: 0,
    maximumFractionDigits: metric.decimals,
  })
}

export function filterByDays(data, days) {
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

export function trendFor(metric, input) {
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

export function trendText(trend) {
  if (trend.change == null) {
    return trend.mode === 'sparse'
      ? `Todavía faltan mediciones para comparar ${trend.currentLabel || 'el periodo reciente'} con una referencia anterior.`
      : 'Aún no hay cobertura suficiente en ambos periodos para calcular una comparación fiable.'
  }
  return `La media de los ${trend.currentLabel} está un ${Math.abs(trend.change).toFixed(1)} % ${trend.change >= 0 ? 'por encima' : 'por debajo'} de los ${trend.baselineLabel}.`
}

export function coverageFor(metric, data, days) {
  if (!data.length) return 'Sin datos'
  if (metric.cadence === 'sparse') return `${data.length} mediciones`
  const first = parseDay(data[0].date)
  const last = parseDay(data.at(-1).date)
  const span = Math.max(1, Math.round((last - first) / 86400000) + 1)
  const expected = days >= 3650 ? span : Math.min(days, span)
  const visible = filterByDays(data, days).length
  return `${Math.round((visible / expected) * 100)} % de cobertura`
}
