import type { Feature, Point } from "geojson"
import type { NormativeMapLayer } from "@/shared/api/normative-map"
import type { useFormatters, useTranslation } from "@/shared/i18n"

export function clusterFeatures(
  layer: NormativeMapLayer,
  t: ReturnType<typeof useTranslation>["t"],
  f: ReturnType<typeof useFormatters>,
): Feature<Point>[] {
  const points = (layer.clusters ?? []).map((cell) => {
    const range =
      cell.minimum !== null && cell.maximum !== null
        ? t(layer.unit === "metres" ? "normative:metreRange" : "normative:minuteRange", {
            min: f.number(cell.minimum, 1),
            max: f.number(cell.maximum, 1),
          })
        : ""
    const detail = t("normative:mapClusterCount", {
      count: f.integer(cell.references),
      known: f.integer(cell.measured),
      unknown: f.integer(cell.references - cell.measured),
    })
    return {
      type: "Feature" as const,
      id: cell.id,
      properties: {
        id: cell.origin_id ?? cell.id,
        kind: "origin",
        state: "unknown",
        count: cell.references,
        cost: cell.maximum,
        range_min: cell.minimum,
        bounds: JSON.stringify(cell.bounds),
        text: [detail, range, cell.references > 1 ? t("normative:mapClusterZoom") : ""]
          .filter(Boolean)
          .join("\n"),
      },
      geometry: { type: "Point" as const, coordinates: [cell.longitude, cell.latitude] },
    }
  })
  const targets = (layer.facilityClusters ?? []).map((cell) => ({
    type: "Feature" as const,
    id: cell.id,
    properties: {
      id: cell.facility_id ?? cell.id,
      kind: "facility",
      state: "facility",
      count: cell.facilities,
      bounds: JSON.stringify(cell.bounds),
      text: [
        t("normative:mapFacilityClusterCount", { count: f.integer(cell.facilities) }),
        cell.facilities > 1 ? t("normative:mapClusterZoom") : "",
      ]
        .filter(Boolean)
        .join("\n"),
    },
    geometry: { type: "Point" as const, coordinates: [cell.longitude, cell.latitude] },
  }))
  return [...points, ...targets]
}
