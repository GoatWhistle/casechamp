import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { useCallback, useEffect, useRef, useState } from "react"
import type { ChatCalculation, CorridorOverlay } from "@/shared/api/chat-calculation"
import { api, unwrap } from "@/shared/api/client"
import type { AnalysisOverlay } from "@/shared/api/road-analysis"
import type { RoadBounds, RoadRenderView, RoadSegment } from "@/shared/api/road-graph"
import { loadRoadView } from "./load-road-view"
import { coversRoadViewport, roadViewport } from "./road-viewport"

export function useRoadGraph() {
  const [showJobOverlay, setShowJobOverlay] = useState(false)
  const [corridorOverlay, setCorridorOverlay] = useState<CorridorOverlay | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const showCalculation = useCallback((calculation: ChatCalculation, instant = false) => {
    setShowJobOverlay(true)
    setCorridorOverlay({ calculation, focus: performance.now(), instant })
    setSelectedJobId(calculation.job_ids[0] ?? null)
  }, [])
  const selectJob = useCallback((id: string) => {
    setShowJobOverlay(true)
    setSelectedJobId(id)
  }, [])
  const [analysisOverlay, setAnalysisOverlay] = useState<AnalysisOverlay | null>(null)
  const [bounds, setBounds] = useState<RoadBounds | null>(null)
  const onBounds = useCallback((next: RoadBounds) => {
    const normalized = roadViewport(next)
    setBounds((previous) =>
      previous && coversRoadViewport(previous, next) ? previous : normalized,
    )
  }, [])
  const [selected, setSelected] = useState<readonly RoadSegment[]>([])
  const [rendering, setRendering] = useState(false)
  const [enabled, setEnabled] = useState(true)
  const view = useQuery<RoadRenderView>({
    queryKey: ["road-graph", bounds],
    placeholderData: keepPreviousData,
    staleTime: Infinity,
    gcTime: 60_000,
    structuralSharing: false,
    enabled: enabled && bounds !== null,
    retry: false,
    queryFn: ({ signal }) => loadRoadView(bounds ?? [0, 0, 1, 1, 8], signal),
  })
  const lastView = useRef<RoadRenderView | undefined>(undefined)
  useEffect(() => {
    if (view.data) lastView.current = view.data
  }, [view.data])
  const job = useQuery({
    queryKey: ["road-scenario", selectedJobId],
    enabled: selectedJobId !== null,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-scenarios/{job_id}", {
          signal,
          params: { path: { job_id: selectedJobId ?? "" } },
        }),
      ),
    refetchInterval: (query) =>
      ["queued", "running"].includes(query.state.data?.status ?? "queued") ? 1500 : false,
  })
  const onRoad = useCallback((road: RoadSegment) => {
    setSelected((current) =>
      current.some((r) => r.way_id === road.way_id)
        ? current.filter((r) => r.way_id !== road.way_id)
        : current.length < 50
          ? [...current, road]
          : current,
    )
  }, [])
  const clear = useCallback(() => setSelected([]), [])
  const clearOverlays = useCallback(() => {
    setCorridorOverlay(null)
    setAnalysisOverlay(null)
    setSelected([])
    setShowJobOverlay(false)
  }, [])
  return {
    clearOverlays,
    hasOverlay: !!corridorOverlay || !!analysisOverlay || !!selected.length || showJobOverlay,
    addition: showJobOverlay ? job.data?.addition : undefined,
    corridorOverlay,
    showCalculation,
    selectJob,
    analysisOverlay,
    setAnalysisOverlay,
    rendering,
    setRendering,
    layerView: enabled ? (view.data ?? lastView.current) : undefined,
    selected,
    enabled,
    setEnabled,
    onBounds,
    onRoad,
    clear,
  }
}

export type RoadGraphState = ReturnType<typeof useRoadGraph>
