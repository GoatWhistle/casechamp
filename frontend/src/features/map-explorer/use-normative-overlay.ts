import { useCallback, useMemo, useState } from "react"
import {
  type Assessment,
  type RegionalRunView,
  useNormativeRoute,
  useRegionalMap,
  useRegionalPoint,
} from "@/entities/normative"
import type {
  NormativeDisplay,
  NormativeRouteStage,
  NormativeView,
  RegionalViewport,
} from "@/shared/api/normative-map"

export function useNormativeOverlay(
  mode: string | null,
  assessment: Assessment | RegionalRunView | null | undefined,
  facilities: Assessment["facilities"] | undefined,
  state: {
    display: NormativeDisplay
    onDisplay: (display: NormativeDisplay) => void
    stage: NormativeRouteStage
    onStage: (stage: NormativeRouteStage) => void
  },
) {
  const { display, stage, onStage } = state
  const regional = assessment && "origins" in assessment ? assessment : null
  const pilot = assessment && "rows" in assessment ? assessment : null
  const [viewport, setViewport] = useState<RegionalViewport | null>(null)
  const [selection, setSelection] = useState({
    point: null as string | null,
    run: undefined as string | null | undefined,
    focus: 0,
    instant: false,
  })
  const run = assessment?.run_id
  const selectedPoint = selection.run === run ? selection.point : null
  const selectPoint = useCallback(
    (id: string, instant = false) =>
      setSelection((current) => ({ point: id, run, focus: current.focus + 1, instant })),
    [run],
  )
  const selectStage = useCallback(
    (next: NormativeRouteStage, instant = false) => {
      onStage(next)
      setSelection((current) => ({ ...current, focus: current.focus + 1, instant }))
    },
    [onStage],
  )
  const selectedRows = stage === "baseline" ? pilot?.baseline_rows : pilot?.rows
  const point = useRegionalPoint(regional?.run_id ?? "", selectedPoint, stage)
  const selected = regional
    ? point.data?.row
    : selectedRows?.find((row) => row.id === selectedPoint)
  const canTrace =
    selected?.routing_node != null && (selected.minutes != null || selected.distance_metres != null)
  const route = useNormativeRoute(
    run ?? "",
    canTrace ? (selected?.id ?? "") : "",
    stage,
    Boolean(regional),
  )
  const map = useRegionalMap(regional?.run_id ?? "", stage, viewport, display !== "index")
  const layer = useMemo(
    () =>
      mode
        ? {
            rows: selectedRows ?? [],
            unit:
              regional?.unit === "metres" || pilot?.criterion.mode === "walk"
                ? ("metres" as const)
                : ("minutes" as const),
            display,
            facilities: pilot?.facilities ?? facilities ?? [],
            onPoint: selectPoint,
            clusters: map.data?.cells,
            facilityClusters: map.data?.facilities,
            onViewport: regional && display !== "index" ? setViewport : undefined,
            route: route.data
              ? { route: route.data, focus: selection.focus, instant: selection.instant }
              : undefined,
          }
        : undefined,
    [
      mode,
      selectedRows,
      display,
      pilot?.facilities,
      pilot?.criterion.mode,
      facilities,
      selectPoint,
      map.data,
      regional,
      route.data,
      selection.focus,
      selection.instant,
    ],
  )
  const range = useMemo(() => {
    const values = regional
      ? map.data?.cells.flatMap((cell) => [cell.minimum, cell.maximum])
      : selectedRows?.map((row) => row.distance_metres ?? row.minutes)
    const known = (values ?? []).filter(
      (value): value is number => value != null && Number.isFinite(value),
    )
    return known.length ? ([Math.min(...known), Math.max(...known)] as const) : null
  }, [regional, map.data, selectedRows])
  const view = buildView(state, regional, pilot, selectedRows, range, map)
  return { selectedPoint, selectPoint, stage, selectStage, layer, view }
}

function buildView(
  state: {
    display: NormativeDisplay
    onDisplay: (display: NormativeDisplay) => void
    stage: NormativeRouteStage
  },
  regional: RegionalRunView | null,
  pilot: Assessment | null,
  selectedRows: Assessment["rows"] | undefined,
  range: readonly [number, number] | null,
  map: ReturnType<typeof useRegionalMap>,
): NormativeView {
  const { display, onDisplay, stage } = state
  return {
    display,
    onDisplay,
    stage,
    range,
    hasResults: regional ? regional.origins > 0 : Boolean(selectedRows?.length),
    unit: regional?.unit === "metres" || pilot?.criterion.mode === "walk" ? "metres" : "minutes",
    clustered: Boolean(regional),
    mapLoading: Boolean(regional) && display !== "index" && map.isFetching,
    mapError: Boolean(regional) && map.isError,
    onMapRetry: () => void map.refetch(),
    viewportReferences: map.isPlaceholderData ? undefined : map.data?.viewport_references,
  }
}
