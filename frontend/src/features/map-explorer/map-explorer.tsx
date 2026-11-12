import { type CSSProperties, type ReactNode, useCallback, useMemo, useRef } from "react"
import { useLocation } from "react-router"
import { boundaryName, type MapControls, modelRegionId, OsmMap } from "@/entities/region"
import { useRoadGraph } from "@/entities/road-graph"
import { usePanelWidth } from "@/shared/hooks"
import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useTranslation } from "@/shared/i18n"
import { PanelResizer, Skeleton } from "@/shared/ui"
import { MapPending } from "./explorer-states"
import { HoverCard } from "./hover-card"
import styles from "./map-explorer.module.css"
import { LinkLayers, MapLegend } from "./map-legend"
import type { MapPanelSlot } from "./map-panel-slot"
import { MapToolbar } from "./map-toolbar"
import { MapZoom } from "./map-zoom"
import { normativeId } from "./metric"
import { OverlayReset, RoadLayer } from "./road-legend"
import { useMapSelection } from "./selection/use-map-selection"
import { useNormativeMapScope } from "./selection/use-regional-scope"
import { OutsideRegion, RegionSummary } from "./summary/region-summary"
import { useExplorerParams } from "./use-explorer-params"
import { useHoverRows } from "./use-hover-rows"
import { useMapData, useSelectedTransit } from "./use-map-data"
import { useMapHover } from "./use-map-hover"
import { useNormativeOverlay } from "./use-normative-overlay"

export interface MapExplorerProps {
  readonly renderPanel: (slot: MapPanelSlot) => ReactNode
}

const PANEL_WIDTH_KEY = "plexus.map-panel-width"

export function MapExplorer({ renderPanel }: MapExplorerProps) {
  const roads = useRoadGraph()
  const { networkMode } = useNetworkMode()
  const fullscreen = useLocation().pathname === "/"
  const { t } = useTranslation()
  const { metric, season, selectedId, setMetric, setSeason, select } = useExplorerParams()
  const { hoveredId, cardRef, point, onHover } = useMapHover()
  const host = useRef<HTMLDivElement | null>(null)
  const panelWidth = usePanelWidth(host, PANEL_WIDTH_KEY)
  const {
    geo,
    regions,
    byId,
    valueAt,
    scale,
    missing,
    failed,
    retry,
    normative,
    normativeTerritory,
    normativeFacilities,
    normativeState,
  } = useMapData(metric, season, selectedId)
  const normativeMode = normativeId(metric)
  const scope = useNormativeMapScope(selectedId, normativeMode, {
    result: normative.data,
    physical: normativeState.display !== "index",
    qualified: normativeState.display === "status",
    territory: normativeTerritory,
    regions: geo.data?.regions,
    facilities: normativeFacilities.data,
  })
  const cameraSelection = scope.selection
  const {
    selectedPoint,
    selectPoint,
    stage,
    selectStage,
    layer: normativeLayer,
    view: normativeView,
  } = useNormativeOverlay(normativeMode, scope.result, scope.facilities, normativeState)
  const modelId = modelRegionId(cameraSelection, regions.data)
  const { links, airports, transit, modelCount, showModels, setShowModels } = useSelectedTransit(
    modelId,
    season,
  )

  const mapTransit = useMemo(
    () => (normativeMode ? { ...transit.data, features: [] } : transit.data),
    [normativeMode, transit.data],
  )
  const mapAirports = useMemo(
    () => (normativeMode && airports.data ? { ...airports.data, airports: [] } : airports.data),
    [normativeMode, airports.data],
  )

  const { mapCommand, setMapCommand, selectRegion, onMapCommand } = useMapSelection(
    geo.data?.regions,
    select,
  )

  const stepOf = useCallback((id: string) => scale.stepOf(valueAt(id)), [scale, valueAt])
  const clear = useCallback(() => selectRegion(null), [selectRegion])
  const controls = useCallback(
    (value: MapControls) => <MapZoom controls={value} onReset={clear} />,
    [clear],
  )

  const hovered = hoveredId ? byId.get(hoveredId) : undefined
  const showRegionHover = !normativeMode || normativeState.display === "index"
  const hoverRows = useHoverRows(
    metric,
    hovered ? valueAt(hovered.id) : null,
    hovered?.hansen ?? null,
  )
  const ready = geo.data !== undefined && regions.data !== undefined
  const transitModes = new Set(transit.data.features.map((feature) => feature.properties?.mode))
  const drawnSymbols = {
    none: missing,
    road: roads.enabled,
    airport: (airports.data?.airports.length ?? 0) > 0,
    air: transitModes.has("air"),
    rail: transitModes.has("rail"),
  }

  const geoRegions = geo.data?.regions
  const regionCard = useCallback(
    (id: string) => {
      if (!regions.data) return <Skeleton lines={4} />
      const model = modelRegionId(id, regions.data)
      if (model) return <RegionSummary id={model} season={season} regions={regions.data} />
      return <OutsideRegion name={boundaryName(id, geoRegions) ?? id} count={regions.data.length} />
    },
    [regions.data, season, geoRegions],
  )

  return (
    <div
      ref={host}
      className={styles.explorer}
      data-fullscreen={fullscreen}
      style={{ "--panel-committed": panelWidth.width } as CSSProperties}
    >
      <div className={styles.stage}>
        {geo.data && regions.data ? (
          <OsmMap
            transit={mapTransit}
            airports={mapAirports}
            normative={normativeLayer}
            roads={{
              view: roads.layerView,
              onRendering: roads.setRendering,
              addition: roads.addition,
              analysis: roads.analysisOverlay,
              corridor: roads.corridorOverlay,
              selected: roads.selected,
              onBounds: roads.onBounds,
              onRoad: roads.onRoad,
            }}
            regions={geo.data.regions}
            stepOf={stepOf}
            selectedId={cameraSelection}
            label={t("map:label")}
            attribution={t("map:attribution")}
            onSelect={selectRegion}
            command={mapCommand}
            onHover={onHover}
            controls={controls}
          />
        ) : (
          <MapPending failed={failed} onRetry={retry} />
        )}
        <div className={styles.overlay}>
          <MapToolbar
            metric={metric}
            season={season}
            onMetric={setMetric}
            onSeason={setSeason}
            regionId={scope.regionId}
            regions={scope.options}
            onRegion={selectRegion}
          />
          {ready ? (
            <MapLegend
              metric={metric}
              scale={scale}
              drawn={drawnSymbols}
              airportsFailed={airports.isError}
              normative={Boolean(normativeMode)}
              normativeView={normativeView}
            >
              <RoadLayer roads={roads} />
              {!normativeMode ? (
                <LinkLayers
                  selected={modelId !== null}
                  loading={links.isPending}
                  failed={links.isError}
                  missing={transit.missing}
                  modelCount={modelCount}
                  showModels={showModels}
                  onModelsChange={setShowModels}
                  onRetry={() => void links.refetch()}
                />
              ) : null}
              <OverlayReset roads={roads} />
            </MapLegend>
          ) : null}
        </div>
        {hovered && showRegionHover ? (
          <HoverCard
            cardRef={cardRef}
            point={point}
            title={hovered.name}
            rows={hoverRows}
            none={t("map:legend.none")}
          />
        ) : null}
      </div>
      <p className="visually-hidden" role="status">
        {modelId && byId.get(modelId)
          ? t("map:selectedStatus", { name: byId.get(modelId)?.name })
          : ""}
      </p>
      {renderPanel({
        normativeId: normativeMode,
        normativeRegionName: scope.regionName,
        normativeRegionId: scope.selection,
        metricLabel: t(`data:metric.${metric}`),
        selectedPoint,
        onPoint: selectPoint,
        onNormativeRegion: selectRegion,
        normativeDisplay: normativeState.display,
        onNormativeDisplay: normativeState.onDisplay,
        routeStage: stage,
        onRouteStage: selectStage,
        regionCard,
        selection: selectedId,
        context: { region_id: modelId, season, network_mode: networkMode, metric },
        onMapCommand,
        roads,
        onChatChange: () => {
          setMapCommand(null)
          roads.clearOverlays()
        },
      })}
      <PanelResizer
        className={styles.resizer}
        width={panelWidth.width}
        min={panelWidth.min}
        max={panelWidth.max}
        label={t("map:panelResize")}
        onPreview={panelWidth.preview}
        onCommit={panelWidth.commit}
        onReset={panelWidth.reset}
      />
    </div>
  )
}
