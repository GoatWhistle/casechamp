import type { FeatureCollection, MultiPolygon } from "geojson"
import type { ExpressionSpecification, StyleSpecification } from "maplibre-gl"
import type { RegionBoundary } from "./boundary-geojson"

export const REGIONS_SOURCE = "regions"
export const CONTEXTUAL_WATER_LAYER = "contextual-water-fill"
export const FILL_LAYER = "region-fill"
export const BORDER_LAYER = "region-border"
export const SELECTED_LAYER = "region-selected"
export const NO_REGION = -1

export interface OsmMapColors {
  readonly fills: readonly string[]
  readonly border: string
  readonly selected: string
  readonly contextBorder?: string
  readonly outside: string
  readonly water: string
}

export function readMapColors(element: HTMLElement): OsmMapColors {
  const style = getComputedStyle(element)
  const token = (name: string) => style.getPropertyValue(name).trim()
  return {
    fills: [
      token("--map-none"),
      ...Array.from({ length: 7 }, (_, index) => token(`--data-seq-${index + 1}`)),
    ],
    border: token("--map-border"),
    selected: token("--map-selected"),
    contextBorder: token("--text-secondary"),
    outside: token("--map-outside"),
    water: token("--map-water"),
  }
}

export function selectionFilter(id: number): ExpressionSpecification {
  return ["==", ["id"], id]
}

function stepColor(fills: readonly string[], key: string): ExpressionSpecification {
  const step: ExpressionSpecification = ["coalesce", ["feature-state", key], 0]
  const branches = fills.slice(1).flatMap((color, index) => [index + 1, color])
  return ["match", step, ...branches, fills[0] ?? "transparent"] as ExpressionSpecification
}

function fillColor(fills: readonly string[]): ExpressionSpecification {
  return [
    "interpolate",
    ["linear"],
    ["coalesce", ["feature-state", "mix"], 1],
    0,
    stepColor(fills, "previous"),
    1,
    stepColor(fills, "step"),
  ]
}

function fillOpacity(): ExpressionSpecification {
  const opacity = (value: number): ExpressionSpecification => [
    "case",
    ["boolean", ["feature-state", "selected"], false],
    0,
    ["boolean", ["feature-state", "hover"], false],
    value * 1.3,
    value,
  ]
  return [
    "interpolate",
    ["linear"],
    ["zoom"],
    3,
    opacity(0.72),
    6,
    opacity(0.5),
    8.5,
    opacity(0.24),
    11,
    opacity(0.06),
  ]
}

const REGION_MAX_ZOOM = 10
const REGION_TOLERANCE = 0.6
const REGION_BUFFER = 32

export function buildStyle(
  colors: OsmMapColors,
  data: FeatureCollection<MultiPolygon>,
  fade: number,
  outsideMask?: MultiPolygon,
  contextualRegions: readonly RegionBoundary[] = [],
  contextualWater: readonly RegionBoundary[] = [],
): StyleSpecification {
  return {
    version: 8,
    sources: {
      osm: { type: "raster", tiles: [__TILE_URL__], tileSize: 256, maxzoom: 19 },
      ...(outsideMask
        ? {
            "outside-regions": {
              type: "geojson" as const,
              data: { type: "Feature" as const, properties: {}, geometry: outsideMask },
              tolerance: 0,
              maxzoom: 18,
            },
          }
        : {}),
      "contextual-water": {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: contextualWater.map((water) => ({
            type: "Feature",
            properties: { name: water.name, display_only: true },
            geometry: { type: "MultiPolygon", coordinates: water.polygons },
          })),
        },
      },
      "contextual-regions": {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: contextualRegions.map((region) => ({
            type: "Feature",
            properties: { name: region.name, display_only: true },
            geometry: { type: "MultiPolygon", coordinates: region.polygons },
          })),
        },
      },
      [REGIONS_SOURCE]: {
        type: "geojson",
        data,
        maxzoom: REGION_MAX_ZOOM,
        tolerance: REGION_TOLERANCE,
        buffer: REGION_BUFFER,
      },
    },
    layers: [
      {
        id: "base",
        type: "background",
        paint: { "background-color": outsideMask ? colors.outside : colors.water },
      },
      {
        id: "osm-tiles",
        type: "raster",
        source: "osm",
        paint: { "raster-fade-duration": fade },
      },
      ...(outsideMask
        ? [
            {
              id: "outside-regions-mask",
              type: "fill" as const,
              source: "outside-regions",
              paint: { "fill-color": colors.outside, "fill-opacity": 1, "fill-antialias": false },
            },
          ]
        : []),
      {
        id: "contextual-region-fill",
        type: "fill",
        source: "contextual-regions",
        paint: {
          "fill-color": colors.fills[3] ?? colors.fills[1] ?? colors.outside,
          "fill-opacity": 0.72,
        },
      },
      {
        id: "contextual-region-border",
        type: "line",
        source: "contextual-regions",
        paint: {
          "line-color": colors.border,
          "line-width": 1.5,
        },
      },
      {
        id: FILL_LAYER,
        type: "fill",
        source: REGIONS_SOURCE,
        paint: { "fill-color": fillColor(colors.fills), "fill-opacity": fillOpacity() },
      },
      {
        id: CONTEXTUAL_WATER_LAYER,
        type: "fill",
        source: "contextual-water",
        paint: { "fill-color": colors.water, "fill-opacity": 1 },
      },
      {
        id: BORDER_LAYER,
        type: "line",
        source: REGIONS_SOURCE,
        paint: {
          "line-color": colors.border,
          "line-width": ["interpolate", ["linear"], ["zoom"], 2, 0.5, 8, 1.6],
        },
      },
      {
        id: SELECTED_LAYER,
        type: "line",
        source: REGIONS_SOURCE,
        filter: selectionFilter(NO_REGION),
        paint: { "line-color": colors.selected, "line-width": 2.5 },
      },
    ],
  }
}
