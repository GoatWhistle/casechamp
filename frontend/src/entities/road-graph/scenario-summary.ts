function precision(value: number): number {
  const size = Math.abs(value)
  if (size === 0 || size >= 1) return 2
  return Math.min(6, Math.ceil(-Math.log10(size)) + 1)
}

export function deltaDigits(value: number): number {
  return Math.max(2, precision(value))
}

export function signed(value: number, format: (value: number, digits?: number) => string): string {
  const text = format(Math.abs(value), precision(value))
  if (value > 0) return `+${text}`
  return value < 0 ? `−${text}` : text
}

export type DeltaTone = "gain" | "loss" | "flat"

export function deltaTone(value: number): DeltaTone {
  if (value > 0) return "gain"
  return value < 0 ? "loss" : "flat"
}
