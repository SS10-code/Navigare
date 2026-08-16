/**
 * Client-side demand forecasting for guest users.
 * Uses simple moving average and linear regression (least squares).
 */

export interface TimeSeriesPoint {
  date: string; // ISO date
  value: number;
}

export interface ForecastResult {
  method: "moving_average" | "linear_regression";
  forecast: Array<{ date: string; predicted: number }>;
  accuracy: number; // R² or MAPE-based score 0-1
}

/**
 * Simple moving average forecast.
 */
export function movingAverageForecast(
  series: TimeSeriesPoint[],
  window: number = 3,
  horizon: number = 7
): ForecastResult {
  if (series.length < window) {
    window = Math.max(1, series.length);
  }

  const recent = series.slice(-window);
  const avg = recent.reduce((sum, p) => sum + p.value, 0) / recent.length;

  const lastDate = series.length ? new Date(series[series.length - 1].date) : new Date();
  const forecast = Array.from({ length: horizon }, (_, i) => {
    const d = new Date(lastDate);
    d.setDate(d.getDate() + i + 1);
    return { date: d.toISOString().split("T")[0], predicted: Math.max(0, Math.round(avg)) };
  });

  return { method: "moving_average", forecast, accuracy: calculateMAE(series, avg) };
}

/**
 * Linear regression (least squares) forecast.
 */
export function linearRegressionForecast(
  series: TimeSeriesPoint[],
  horizon: number = 7
): ForecastResult {
  const n = series.length;
  if (n < 2) {
    return movingAverageForecast(series, n, horizon);
  }

  const x = series.map((_, i) => i);
  const y = series.map((p) => p.value);

  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((a, xi, i) => a + xi * y[i], 0);
  const sumXX = x.reduce((a, xi) => a + xi * xi, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  const r2 = calculateR2(y, x.map((xi) => slope * xi + intercept));

  const lastDate = new Date(series[series.length - 1].date);
  const forecast = Array.from({ length: horizon }, (_, i) => {
    const d = new Date(lastDate);
    d.setDate(d.getDate() + i + 1);
    const predicted = slope * (n + i) + intercept;
    return { date: d.toISOString().split("T")[0], predicted: Math.max(0, Math.round(predicted)) };
  });

  return { method: "linear_regression", forecast, accuracy: r2 };
}

function calculateR2(actual: number[], predicted: number[]): number {
  const mean = actual.reduce((a, b) => a + b, 0) / actual.length;
  const ssRes = actual.reduce((sum, val, i) => sum + (val - predicted[i]) ** 2, 0);
  const ssTot = actual.reduce((sum, val) => sum + (val - mean) ** 2, 0);
  return ssTot === 0 ? 1 : Math.max(0, 1 - ssRes / ssTot);
}

function calculateMAE(series: TimeSeriesPoint[], baseline: number): number {
  if (!series.length) return 0;
  const mae = series.reduce((sum, p) => sum + Math.abs(p.value - baseline), 0) / series.length;
  const range = Math.max(...series.map((p) => p.value)) - Math.min(...series.map((p) => p.value));
  return range === 0 ? 1 : Math.max(0, 1 - mae / range);
}
