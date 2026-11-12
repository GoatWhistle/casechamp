import type { ReactNode } from "react"
import type { RoadGraphState } from "@/entities/road-graph"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import type { ChatContext } from "@/shared/api/chat-stream"
import type { NormativeDisplay, NormativeRouteStage } from "@/shared/api/normative-map"

export interface MapPanelSlot {
  readonly normativeDisplay: NormativeDisplay
  readonly onNormativeDisplay: (display: NormativeDisplay) => void
  readonly routeStage: NormativeRouteStage
  readonly onRouteStage: (stage: NormativeRouteStage, instant?: boolean) => void
  readonly onPoint: (id: string, instant?: boolean) => void
  readonly onNormativeRegion: (id: string | null) => void
  readonly normativeRegionId: string | null
  readonly normativeRegionName: string | null
  readonly normativeId: string | null
  readonly metricLabel: string
  readonly selectedPoint: string | null
  readonly regionCard: (id: string) => ReactNode
  readonly selection: string | null
  readonly context: ChatContext
  readonly onMapCommand: MapCommandHandler
  readonly roads: RoadGraphState
  readonly onChatChange: () => void
}
