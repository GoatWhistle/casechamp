import { type CSSProperties, type ReactNode, useCallback, useRef, useState } from "react"
import { useLocation } from "react-router"
import { boundaryName, type MapControls, modelRegionId, OsmMap } from "@/entities/region"
import { type RoadGraphState, useRoadGraph } from "@/entities/road-graph"
import type { ChatMapCommand, MapCommandHandler } from "@/shared/api/chat-map"
import type { ChatContext } from "@/shared/api/chat-stream"
import { usePanelWidth } from "@/shared/hooks"
import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { PanelResizer, Skeleton } from "@/shared/ui"
import { MapPending } from "./explorer-states"
import { HoverCard } from "./hover-card"
import styles from "./map-explorer.module.css"
import { LinkLayers, MapLegend } from "./map-legend"
import { MapToolbar } from "./map-toolbar"
import { MapZoom } from "./map-zoom"
import { formatMetric, metricValue } from "./metric"
import { OverlayReset, RoadLayer } from "./road-legend"
import { OutsideRegion, RegionSummary } from "./summary/region-summary"
import { useExplorerParams } from "./use-explorer-params"
import { useMapData, useSelectedTransit } from "./use-map-data"
import { useMapHover } from "./use-map-hover"

export interface MapPanelSlot {
  readonly regionCard: (id: string) => ReactNode
  readonly selection: string | null
  readonly context: ChatContext
  readonly onMapCommand: MapCommandHandler
  readonly roads: RoadGraphState
  readonly onChatChange: () => void
}

export interface MapExplorerProps {
  readonly renderPanel: (slot: MapPanelSlot) => ReactNode
}

const PANEL_WIDTH_KEY = "plexus.map-panel-width"

export function MapExplorer({ renderPanel }: MapExplorerProps) {
  const roads = useRoadGraph()
  const { networkMode } = useNetworkMode()
  const fullscreen = useLocation().pathname === "/"
  const { t } = useTranslation()
  const f = useFormatters()
  const { metric, season, selectedId, setMetric, setSeason, select } = useExplorerParams()
  const { hoveredId, cardRef, point, onHover } = useMapHover()
  const host = useRef<HTMLDivElement | null>(null)
  const panelWidth = usePanelWidth(host, PANEL_WIDTH_KEY)
  const { geo, regions, byId, valueAt, scale, missing, failed, retry } = useMapData(metric, season)
  const modelId = modelRegionId(selectedId, regions.data)
  const { links, airports, transit, modelCount, showModels, setShowModels } = useSelectedTransit(
    modelId,
    season,
  )

  const [mapCommand, setMapCommand] = useState<ChatMapCommand | null>(null)
  const selectRegion = useCallback(
    (id: string | null) => {
      setMapCommand(null)
      select(id)
    },
    [select],
  )
  const onMapCommand = useCallback<MapCommandHandler>(
    (command) => {
      if (command.action === "focus") {
        if (!command.region_ids.every((id) => geo.data?.regions.some((region) => region.id === id)))
          return
        select(command.region_ids.length === 1 ? (command.region_ids[0] ?? null) : null)
      }
      if (command.action === "reset") select(null)
      setMapCommand({ ...command })
    },
    [geo.data, select],
  )

  const stepOf = useCallback((id: string) => scale.stepOf(valueAt(id)), [scale, valueAt])
  const clear = useCallback(() => selectRegion(null), [selectRegion])
  const controls = useCallback(
    (value: MapControls) => <MapZoom controls={value} onReset={clear} />,
    [clear],
  )

  const hovered = hoveredId ? byId.get(hoveredId) : undefined
  const hoveredIndex = hovered ? hovered.hansen : null
  const hoveredValue = hovered ? metricValue(hovered, metric) : null
  const indexRow = {
    key: "hansen",
    label: t("data:metric.hansen"),
    value: hoveredIndex === null ? null : formatMetric(hoveredIndex, "hansen", f),
  }
  const metricRow = {
    key: metric,
    label: t(`data:metric.${metric}`),
    value: hoveredValue === null ? null : formatMetric(hoveredValue, metric, f),
  }
  const hoverRows = metric === "hansen" ? [indexRow] : [indexRow, metricRow]
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
            transit={transit.data}
            airports={airports.data}
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
            selectedId={selectedId}
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
          <MapToolbar metric={metric} season={season} onMetric={setMetric} onSeason={setSeason} />
          {ready ? (
            <MapLegend
              metric={metric}
              scale={scale}
              drawn={drawnSymbols}
              airportsFailed={airports.isError}
            >
              <RoadLayer roads={roads} />
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
              <OverlayReset roads={roads} />
            </MapLegend>
          ) : null}
        </div>
        {hovered ? (
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
