import type { FeatureCollection, LineString, MultiPolygon } from "geojson"
import {
  Map as LibreMap,
  type MapLayerMouseEvent,
  type MapOptions,
  setWorkerUrl,
} from "maplibre-gl"
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url"
import { useCallback, useEffect, useRef, useState } from "react"
import type { AirportCatalog } from "@/shared/api/airports"
import type { ChatMapCommand } from "@/shared/api/chat-map"
import type { MunicipalityLayer } from "@/shared/api/municipalities"
import type { NormativeMapLayer } from "@/shared/api/normative-map"
import type { RoadLayerProps } from "@/shared/api/road-graph"
import { motionMs, useReducedMotion } from "@/shared/motion"
import type { BoundaryAtlas, RegionBoundary } from "./boundary-geojson"
import { HOME_PADDING, MIN_MAP_ZOOM, resizeMapView } from "./camera/national-view"
import { useMapControls } from "./camera/use-map-controls"
import { useJourneyPoints } from "./journey/use-journey-points"
import { aimCamera, corners, FLAT_MAP, keepFlat, roamConstrain } from "./map-camera"

import { bindHover } from "./map-hover"
import { useMunicipalityLayer } from "./municipalities/use-municipality-layer"
import { useNormativeLayer } from "./normative-layer/use-normative-layer"
import { buildStyle, FILL_LAYER, REGIONS_SOURCE, readMapColors } from "./osm-style"
import { blocksRegionSelection } from "./paint/map-hit-test"
import { recolorRegions, regionSteps } from "./paint/recolor"
import { useAirportLayer } from "./use-airport-layer"
import { useRoadLayer } from "./use-road-layer"
import { useSettlementFocus } from "./use-settlement-focus"
import { useTransitLayer } from "./use-transit-layer"

export type { MapControls } from "./camera/use-map-controls"

setWorkerUrl(workerUrl)
const TILE_CACHE = 1024
const MIN_ZOOM = MIN_MAP_ZOOM
const MAX_ZOOM = 18
export type MapStep = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7

export interface OsmMapOptions {
  readonly contextualWater?: readonly RegionBoundary[] | undefined
  readonly contextualRegions?: readonly RegionBoundary[] | undefined
  readonly outsideMask?: MultiPolygon | undefined
  readonly municipalities?: MunicipalityLayer | undefined
  readonly normative?: NormativeMapLayer | undefined
  readonly airports?: AirportCatalog | undefined
  readonly transit: FeatureCollection<LineString>
  readonly roads?: RoadLayerProps | undefined
  readonly atlas: BoundaryAtlas
  readonly stepOf: (id: string) => number
  readonly command?: ChatMapCommand | null | undefined
  readonly selectedId: string | null
  readonly onSelect: (id: string) => void
  readonly onHover: (id: string | null, x: number, y: number) => void
  readonly label: string
}

export function useOsmMap({
  contextualWater,
  contextualRegions,
  outsideMask,
  municipalities,
  normative,
  airports,
  transit,
  roads,
  atlas,
  stepOf,
  selectedId,
  command,
  onSelect,
  onHover,
  label,
}: OsmMapOptions) {
  const container = useRef<HTMLDivElement | null>(null)
  const engine = useRef<LibreMap | null>(null)
  const [styleReady, setStyleReady] = useState(false)
  useRoadLayer(engine, roads, styleReady)
  useTransitLayer(engine, transit, styleReady)
  const airportHover = useAirportLayer(engine, airports, styleReady)
  useSettlementFocus(engine, command, styleReady)
  useJourneyPoints(engine, styleReady)
  useNormativeLayer(engine, normative, styleReady)
  useMunicipalityLayer(engine, municipalities, styleReady)
  const roadState = useRef(roads)
  roadState.current = roads
  const ready = useRef(false)
  const appliedCommand = useRef<ChatMapCommand | null | undefined>(undefined)
  const hovered = useRef<number | null>(null)
  const reduced = useReducedMotion()
  const state = useRef({ atlas, stepOf, selectedId, command, onSelect, onHover, reduced })
  state.current = { atlas, stepOf, selectedId, command, onSelect, onHover, reduced }
  const duration = useCallback(
    (instant?: boolean, command = false) =>
      instant || state.current.reduced
        ? 0
        : motionMs(command ? "--dur-map" : "--dur-panel", container.current ?? undefined),
    [],
  )

  const painted = useRef(new Map<number, number>())
  const stopRecolor = useRef<() => void>(() => undefined)
  const paintSteps = useCallback(() => {
    const map = engine.current
    if (!map || !ready.current) return
    const steps = regionSteps(state.current.atlas.featureOf, state.current.stepOf)
    stopRecolor.current()
    const instant = state.current.reduced || painted.current.size === 0
    stopRecolor.current = recolorRegions(map, steps, painted.current, instant)
  }, [])

  const setHover = useCallback((id: number | null) => {
    const map = engine.current
    if (!map || !ready.current || hovered.current === id) return
    if (hovered.current !== null)
      map.setFeatureState({ source: REGIONS_SOURCE, id: hovered.current }, { hover: false })
    if (id !== null) map.setFeatureState({ source: REGIONS_SOURCE, id }, { hover: true })
    map.getCanvas().style.cursor = id === null ? "" : "pointer"
    hovered.current = id
  }, [])

  const aim = useCallback(
    (instant?: boolean) => {
      const map = engine.current
      if (!map || !ready.current) return
      const current = state.current
      const action = current.command !== appliedCommand.current ? current.command : undefined
      appliedCommand.current = current.command
      if (!action && ["focus_settlement", "focus_road"].includes(current.command?.action ?? ""))
        return
      aimCamera(
        map,
        current.atlas,
        action,
        current.selectedId,
        duration(instant, Boolean(action)),
        duration(instant),
      )
    },
    [duration],
  )
  useEffect(() => {
    const element = container.current
    if (!element || atlas.collection.features.length === 0) return
    const limits = { min: MIN_ZOOM, max: MAX_ZOOM }
    const options: MapOptions = {
      container: element,
      style: buildStyle(
        readMapColors(element),
        atlas.collection,
        state.current.reduced ? 0 : motionMs("--dur-base", element),
        outsideMask,
        contextualRegions,
        contextualWater,
      ),
      bounds: corners(atlas.home),
      fitBoundsOptions: { padding: HOME_PADDING },
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      transformConstrain: roamConstrain(atlas.home, limits),
      attributionControl: false,
      ...FLAT_MAP,
      locale: { "Map.Title": label },
      fadeDuration: state.current.reduced ? 0 : motionMs("--dur-fast", element),
      maxTileCacheSize: TILE_CACHE,
      refreshExpiredTiles: false,
    }
    const map = keepFlat(new LibreMap(options))
    engine.current = map
    let width = element.clientWidth
    const resize = new ResizeObserver(() => {
      const shift = (element.clientWidth - width) / 2
      width = element.clientWidth
      const national = resizeMapView(map, state.current.atlas.home, ready.current)
      if (!national && shift !== 0) map.panBy([shift, 0], { animate: false })
    })
    resize.observe(element)
    const onClick = (event: MapLayerMouseEvent) => {
      if (blocksRegionSelection(map, event.point)) return
      const id = event.features?.[0]?.id
      const region = typeof id === "number" ? state.current.atlas.regionOf.get(id) : undefined
      if (region) state.current.onSelect(region)
    }
    const markView = () => {
      const box = map.getBounds()
      roadState.current?.onBounds([
        Math.max(-180, box.getWest()),
        Math.max(-85, box.getSouth()),
        Math.min(180, box.getEast()),
        Math.min(85, box.getNorth()),
        map.getZoom(),
      ])
      element.dataset.zoom = map.getZoom().toFixed(3)
      const center = map.getCenter()
      element.dataset.center = `${center.lng.toFixed(3)},${center.lat.toFixed(3)}`
    }
    map.on("style.load", () => {
      ready.current = true
      setStyleReady(true)
      paintSteps()
      aim(true)
      markView()
    })
    map.on("moveend", markView)
    const disposeHover = bindHover(
      map,
      setHover,
      (region, x, y) => state.current.onHover(region, x, y),
      (id) => (id === null ? null : (state.current.atlas.regionOf.get(id) ?? null)),
      (feature) => airportHover.current(feature),
      motionMs("--dur-instant", element),
    )
    map.on("click", FILL_LAYER, onClick)
    return () => {
      disposeHover()
      ready.current = false
      setStyleReady(false)
      appliedCommand.current = undefined
      hovered.current = null
      engine.current = null
      resize.disconnect()
      map.remove()
    }
  }, [
    atlas,
    contextualWater,
    contextualRegions,
    outsideMask,
    paintSteps,
    aim,
    setHover,
    label,
    airportHover,
  ])

  // biome-ignore lint/correctness/useExhaustiveDependencies: Repaint when data read through the latest-state ref changes.
  useEffect(() => {
    paintSteps()
  }, [paintSteps, atlas, stepOf])

  // biome-ignore lint/correctness/useExhaustiveDependencies: Ref-backed camera callback must react to selection changes.
  useEffect(() => {
    aim()
  }, [aim, atlas, selectedId, command])

  const controls = useMapControls(engine, atlas.home, duration)

  return { container, controls }
}
