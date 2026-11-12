import type { FeatureCollection, Point } from "geojson"
import type { ExpressionSpecification } from "maplibre-gl"
import type { NormativeDisplay } from "@/shared/api/normative-map"

export function normativePointColor(
  data: FeatureCollection<Point>,
  display: NormativeDisplay | undefined,
  color: (key: string) => string,
): ExpressionSpecification | string {
  if (display !== "travel")
    return [
      "match",
      ["get", "state"],
      "within",
      color("--status-success"),
      "exceeded",
      color("--status-danger"),
      "unreachable",
      color("--status-danger"),
      color("--text-muted"),
    ]
  let min = Infinity
  let max = -Infinity
  for (const feature of data.features) {
    const value = feature.properties?.cost
    if (typeof value !== "number" || !Number.isFinite(value)) continue
    const lower = feature.properties?.range_min
    min = Math.min(min, typeof lower === "number" ? lower : value)
    max = Math.max(max, value)
  }
  if (!Number.isFinite(min)) return color("--text-muted")
  const numeric: ExpressionSpecification | string =
    min === max
      ? color("--data-seq-4")
      : [
          "interpolate",
          ["linear"],
          ["coalesce", ["get", "cost"], min],
          min,
          color("--data-seq-2"),
          (min + max) / 2,
          color("--data-seq-4"),
          max,
          color("--data-seq-7"),
        ]
  return ["case", ["==", ["get", "cost"], null], color("--text-muted"), numeric]
}
