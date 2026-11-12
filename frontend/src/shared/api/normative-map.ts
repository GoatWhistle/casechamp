import type { components } from "./schema.gen"

export type NormativeDisplay = "index" | "travel" | "status"

export interface NormativeView {
  readonly clustered?: boolean | undefined
  readonly mapLoading?: boolean | undefined
  readonly mapError?: boolean | undefined
  readonly onMapRetry?: (() => void) | undefined
  readonly viewportReferences?: number | undefined
  readonly display: NormativeDisplay
  readonly stage: NormativeRouteStage
  readonly hasResults: boolean
  readonly onDisplay: (display: NormativeDisplay) => void
  readonly range: readonly [number, number] | null
  readonly unit: "minutes" | "metres"
}

export interface RegionalViewport {
  readonly west: number
  readonly south: number
  readonly east: number
  readonly north: number
  readonly zoom: number
}

export interface NormativeMapLayer {
  readonly unit?: "minutes" | "metres" | undefined
  readonly clusters?: components["schemas"]["RegionalMapCellResponse"][] | undefined
  readonly facilityClusters?: components["schemas"]["RegionalFacilityCellResponse"][] | undefined
  readonly onViewport?: ((viewport: RegionalViewport) => void) | undefined
  readonly display?: NormativeDisplay | undefined
  readonly rows: components["schemas"]["AccessResponse"][]
  readonly facilities: components["schemas"]["FacilityResponse"][]
  readonly route?: NormativeRouteOverlay | undefined
  readonly onPoint: (id: string) => void
}

export type NormativeRouteStage = components["schemas"]["NormativeRouteResponse"]["stage"]

export interface NormativeRouteOverlay {
  readonly route: components["schemas"]["NormativeRouteResponse"]
  readonly focus: number
  readonly instant: boolean
}
