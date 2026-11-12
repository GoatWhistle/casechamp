import type { FeatureCollection, Point } from "geojson"
import { expect, it } from "vitest"
import { normativePointColor } from "@/entities/region/osm-map/normative-layer/normative-point-color"

const data: FeatureCollection<Point> = {
  type: "FeatureCollection",
  features: [10, 40, null].map((cost, index) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [65, 55] },
    properties: { id: index, kind: "origin", state: "unknown", cost },
  })),
}

it("renders available travel numbers with a numeric scale even when all legal statuses are unknown", () => {
  const paint = normativePointColor(data, "travel", (token) => token)
  expect(paint).toEqual([
    "case",
    ["==", ["get", "cost"], null],
    "--text-muted",
    [
      "interpolate",
      ["linear"],
      ["coalesce", ["get", "cost"], 10],
      10,
      "--data-seq-2",
      25,
      "--data-seq-4",
      40,
      "--data-seq-7",
    ],
  ])
})

it("retains the legal status palette only in the explicit status view", () => {
  expect(normativePointColor(data, "status", (token) => token)).toEqual([
    "match",
    ["get", "state"],
    "within",
    "--status-success",
    "exceeded",
    "--status-danger",
    "unreachable",
    "--status-danger",
    "--text-muted",
  ])
})

it("keeps missing paths grey and handles uniform data without invalid interpolation stops", () => {
  expect(normativePointColor({ type: "FeatureCollection", features: [] }, "travel", (x) => x)).toBe(
    "--text-muted",
  )
  expect(
    normativePointColor({ ...data, features: data.features.slice(0, 1) }, "travel", (x) => x),
  ).toEqual(["case", ["==", ["get", "cost"], null], "--text-muted", "--data-seq-4"])
})
