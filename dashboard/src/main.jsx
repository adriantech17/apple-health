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

import {
  GROUPS,
  METRICS,
  METRIC_BY_ID,
  METRIC_GUIDE,
  NOTES,
  PRIMARY_IDS,
  RANGES,
  SLEEP_STAGES,
} from './metricCatalog'
import {
  coverageFor,
  filterByDays,
  formatValue,
  parseDay,
  trendFor,
  trendText,
} from './lib/metricAnalysis'

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
