import { describe, expect, it } from 'vitest'
import { coverageFor, dayKey, filterByDays, trendFor } from './metricAnalysis'

const dailyMetric = { cadence: 'daily' }
const sparseMetric = { cadence: 'sparse' }

function shiftDate(date, amount) {
  const shifted = new Date(date)
  shifted.setDate(shifted.getDate() + amount)
  return shifted
}

function relativePoint(base, daysAgo, value) {
  return { date: dayKey(shiftDate(base, -daysAgo)), value }
}

describe('filterByDays', () => {
  it('keeps an inclusive window anchored to the latest observation', () => {
    const data = Array.from({ length: 10 }, (_, index) => ({
      date: `2026-07-${String(index + 1).padStart(2, '0')}`,
      value: index + 1,
    }))

    expect(filterByDays(data, 3).map((point) => point.date)).toEqual([
      '2026-07-08',
      '2026-07-09',
      '2026-07-10',
    ])
  })
})

describe('trendFor', () => {
  it('compares seven recent daily values with the preceding 28 days', () => {
    const latest = new Date(2026, 6, 15, 12)
    const data = Array.from({ length: 35 }, (_, index) => {
      const daysAgo = 34 - index
      return relativePoint(latest, daysAgo, daysAgo <= 6 ? 110 : 100)
    })

    const trend = trendFor(dailyMetric, data)

    expect(trend.currentCount).toBe(7)
    expect(trend.baselineCount).toBe(28)
    expect(trend.current).toBe(110)
    expect(trend.baseline).toBe(100)
    expect(trend.change).toBeCloseTo(10)
    expect(trend.direction).toBe('up')
  })

  it('excludes today from metrics that only compare complete days', () => {
    const today = new Date()
    const data = Array.from({ length: 36 }, (_, index) => {
      const daysAgo = 35 - index
      const value = daysAgo === 0 ? 1000 : daysAgo <= 7 ? 110 : 100
      return relativePoint(today, daysAgo, value)
    })

    const trend = trendFor({ cadence: 'daily', completeDaysOnly: true }, data)

    expect(trend.currentCount).toBe(7)
    expect(trend.baselineCount).toBe(28)
    expect(trend.current).toBe(110)
    expect(trend.change).toBeCloseTo(10)
  })

  it('uses wider windows for sparse measurements', () => {
    const latest = new Date(2026, 6, 15, 12)
    const data = [
      relativePoint(latest, 200, 40),
      relativePoint(latest, 150, 42),
      relativePoint(latest, 30, 50),
      relativePoint(latest, 0, 52),
    ]

    const trend = trendFor(sparseMetric, data)

    expect(trend.currentCount).toBe(2)
    expect(trend.baselineCount).toBe(2)
    expect(trend.current).toBe(51)
    expect(trend.baseline).toBe(41)
    expect(trend.change).toBeCloseTo(24.3902)
    expect(trend.direction).toBe('up')
  })

  it('does not infer a sparse trend without two values in each period', () => {
    const latest = new Date(2026, 6, 15, 12)
    const data = [relativePoint(latest, 150, 40), relativePoint(latest, 0, 50)]

    const trend = trendFor(sparseMetric, data)

    expect(trend.change).toBeNull()
    expect(trend.currentCount).toBe(1)
    expect(trend.baselineCount).toBe(1)
    expect(trend.direction).toBe('neutral')
  })
})

describe('coverageFor', () => {
  it('reports missing daily observations within the visible span', () => {
    const data = [
      { date: '2026-07-01', value: 1 },
      { date: '2026-07-02', value: 1 },
      { date: '2026-07-04', value: 1 },
      { date: '2026-07-05', value: 1 },
    ]

    expect(coverageFor(dailyMetric, data, 5)).toBe('80 % de cobertura')
  })

  it('reports the number of sparse measurements instead of daily coverage', () => {
    const data = [
      { date: '2026-01-01', value: 40 },
      { date: '2026-04-01', value: 42 },
    ]

    expect(coverageFor(sparseMetric, data, 365)).toBe('2 mediciones')
  })
})
