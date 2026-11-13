import type { Map as LibreMap } from "maplibre-gl"
import { motionMs } from "@/shared/motion"
import { fitPadding } from "../camera/fit-padding"

export function focusCluster(
  map: LibreMap,
  properties: Readonly<Record<string, unknown>> | undefined,
  reduced: boolean,
): boolean {
  if (Number(properties?.count ?? 1) <= 1) return false
  const bounds = parseBounds(properties?.bounds)
  if (!bounds) return false
  const [west, south, east, north] = bounds
  map.stop()
  map.fitBounds(
    [
      [west, south],
      [east, north],
    ],
    {
      padding: fitPadding(map, 96),
      maxZoom: Math.min(18, map.getZoom() + 3),
      duration: reduced ? 0 : motionMs("--dur-panel", map.getContainer()),
    },
  )
  return true
}

function parseBounds(value: unknown): [number, number, number, number] | null {
  if (typeof value !== "string") return null
  try {
    const bounds: unknown = JSON.parse(value)
    if (
      Array.isArray(bounds) &&
      bounds.length === 4 &&
      bounds.every((item) => typeof item === "number" && Number.isFinite(item))
    )
      return bounds as [number, number, number, number]
  } catch {
    return null
  }
  return null
}
