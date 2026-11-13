import { useCallback, useMemo } from "react"
import type { RoadGraphState } from "@/entities/road-graph"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import type { PanelDockState } from "./use-panel-dock"

type ShowCalculation = RoadGraphState["showCalculation"]

export function useSheetReveal(
  dock: PanelDockState,
  onMapCommand: MapCommandHandler,
  roads: RoadGraphState,
) {
  const { reveal } = dock
  const command = useCallback<MapCommandHandler>(
    (value) => {
      reveal()
      onMapCommand(value)
    },
    [reveal, onMapCommand],
  )
  const shown = useMemo<RoadGraphState>(() => {
    const showCalculation: ShowCalculation = (calculation, instant) => {
      reveal()
      roads.showCalculation(calculation, instant)
    }
    return { ...roads, showCalculation }
  }, [roads, reveal])
  return { onMapCommand: command, roads: shown }
}
