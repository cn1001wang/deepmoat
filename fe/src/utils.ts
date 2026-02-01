export function toFixed(num: number, decimalPlaces: number): number {
  const factor = 10 ** decimalPlaces
  return Math.round(num * factor) / factor
}
