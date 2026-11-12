import type { FeatureCollection, Point } from "geojson"
import type { NormativeMapLayer } from "@/shared/api/normative-map"
import type { useFormatters, useTranslation } from "@/shared/i18n"
import { clusterFeatures } from "./normative-cluster-data"

export function buildData(
  assessment: NormativeMapLayer,
  t: ReturnType<typeof useTranslation>["t"],
  f: ReturnType<typeof useFormatters>,
): FeatureCollection<Point> {
  const data: FeatureCollection<Point> = { type: "FeatureCollection", features: [] }
  for (const point of assessment.rows) {
    if (point.latitude === null || point.longitude === null) continue
    const detail = t("normative:pointDetail", {
      name: point.name,
      state: t(`normative:states.${point.state}`),
    })
    const cost = pointCost(point, t, f)
    data.features.push({
      type: "Feature",
      id: point.id,
      properties: {
        id: point.id,
        kind: "origin",
        state: point.state,
        cost: point.distance_metres ?? point.minutes,
        text: [detail, cost].filter(Boolean).join("\n"),
      },
      geometry: { type: "Point", coordinates: [point.longitude, point.latitude] },
    })
  }
  for (const point of assessment.facilities) {
    if (point.latitude === null || point.longitude === null) continue
    data.features.push({
      type: "Feature",
      properties: {
        id: point.id,
        kind: "facility",
        state: "facility",
        text: `${point.name || t("normative:unnamedFacility")}\n${point.address}`,
      },
      geometry: { type: "Point", coordinates: [point.longitude, point.latitude] },
    })
  }
  data.features.push(...clusterFeatures(assessment, t, f))
  return data
}

function pointCost(
  point: NormativeMapLayer["rows"][number],
  t: ReturnType<typeof useTranslation>["t"],
  f: ReturnType<typeof useFormatters>,
) {
  if (point.distance_metres != null)
    return t("normative:pointMetres", { value: f.number(point.distance_metres, 1) })
  return point.minutes === null
    ? ""
    : t("normative:pointMinutes", { value: f.number(point.minutes, 1) })
}
