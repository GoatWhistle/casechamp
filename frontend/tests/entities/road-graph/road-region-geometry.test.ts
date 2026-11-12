import { expect, it } from "vitest"
import { prepareRegionIntersection } from "@/entities/road-graph/road-region-geometry"
import { prepareRoadView } from "@/entities/road-graph/road-render-data"
import type { RoadFocus, RoadSegment } from "@/shared/api/road-graph"

const focus: RoadFocus = {
  id: "one",
  polygons: [
    [
      [
        [0, 0],
        [10, 0],
        [10, 10],
        [0, 10],
        [0, 0],
      ],
      [
        [4, 4],
        [6, 4],
        [6, 6],
        [4, 6],
        [4, 4],
      ],
    ],
  ],
}

it("detects actual border crossings with both endpoints outside and excludes a polygon hole", () => {
  const intersects = prepareRegionIntersection(focus)
  expect(
    intersects([
      [-2, 2],
      [12, 2],
    ]),
  ).toBe(true)
  expect(
    intersects([
      [1, 1],
      [2, 2],
    ]),
  ).toBe(true)
  expect(
    intersects([
      [4.5, 5],
      [5.5, 5],
    ]),
  ).toBe(false)
  expect(
    intersects([
      [-2, -1],
      [12, -1],
    ]),
  ).toBe(false)
})

it("compares eastern longitudes without inventing an antimeridian crossing", () => {
  const intersects = prepareRegionIntersection({
    id: "east",
    polygons: [
      [
        [
          [178, 60],
          [184, 60],
          [184, 70],
          [178, 70],
          [178, 60],
        ],
      ],
    ],
  })
  expect(
    intersects([
      [179, 65],
      [-179, 65],
    ]),
  ).toBe(true)
  expect(
    intersects([
      [30, 65],
      [31, 65],
    ]),
  ).toBe(false)
})

it("retains loaded continuing chains of a real crossing OSM way and preserves original geometry", async () => {
  const road = (way_id: number, coordinates: number[][], highway = "residential"): RoadSegment => ({
    way_id,
    coordinates,
    highway,
    name: "Road",
    speed_kmh: 40,
  })
  const segments = [
    road(1, [
      [-2, 2],
      [12, 2],
    ]),
    road(1, [
      [12, 2],
      [14, 2],
    ]),
    road(2, [
      [12, 4],
      [14, 4],
    ]),
    road(3, [
      [4.5, 5],
      [5.5, 5],
    ]),
  ]
  const view = prepareRoadView(
    { segments, matched: 4, truncated: false, version: "v", detail: "all" },
    focus,
  )
  const data = JSON.parse(await (view.geometry[0]?.text() ?? Promise.resolve("{}")))
  expect(
    data.features.map(
      (feature: { properties: { focus_connected: boolean } }) => feature.properties.focus_connected,
    ),
  ).toEqual([true, true, false, false])
  expect(
    data.features.map(
      (feature: { geometry: { coordinates: number[][] } }) => feature.geometry.coordinates,
    ),
  ).toEqual(segments.map((segment) => segment.coordinates))
  expect(view.focusRegionId).toBe("one")
})
