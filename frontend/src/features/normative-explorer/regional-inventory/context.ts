import type { NormativeDisplay, NormativeRouteStage } from "@/shared/api/normative-map"
import type { RoadSegment } from "@/shared/api/road-graph"

export interface RegionalInventoryContext {
  readonly display?: NormativeDisplay | undefined
  readonly onDisplay?: ((display: NormativeDisplay) => void) | undefined
  readonly regionId?: string | null | undefined
  readonly criterionId: string
  readonly roads: readonly RoadSegment[]
  readonly selectedPoint: string | null
  readonly onPoint: (id: string, instant?: boolean) => void
  readonly routeStage: NormativeRouteStage
  readonly onRouteStage: (stage: NormativeRouteStage, instant?: boolean) => void
}
