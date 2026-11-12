import clsx from "clsx"
import { type ReactNode, useId, useRef, useState } from "react"
import { useMediaQuery } from "@/shared/hooks"
import { type MessageKey, useFormatters, useTranslation } from "@/shared/i18n"
import { Swap, useLatched, usePresence } from "@/shared/motion"
import { Button, Disclosure, Popover, Switch } from "@/shared/ui"
import { LegendPanel } from "./legend/legend-panel"
import { TrafficKey } from "./legend/traffic-key"
import styles from "./map-legend.module.css"
import { formatThreshold, type MetricKey } from "./metric"
import type { MetricScale } from "./scale"

const WIDE = "(min-width: 64rem)"

export type MapSymbol = "none" | "road" | "airport" | "air" | "rail"

const SYMBOLS: readonly MapSymbol[] = ["none", "road", "airport", "air", "rail"]

const SYMBOL_LABEL: Readonly<Record<MapSymbol, MessageKey>> = {
  none: "map:legend.none",
  road: "map:legend.roads",
  airport: "map:legend.airports",
  air: "data:mode.air",
  rail: "data:mode.rail",
}

export interface MapLegendProps {
  readonly metric: MetricKey
  readonly scale: MetricScale
  readonly drawn: Readonly<Record<MapSymbol, boolean>>
  readonly airportsFailed: boolean
  readonly children: ReactNode
}

export function MapLegend({ metric, scale, drawn, airportsFailed, children }: MapLegendProps) {
  const { t } = useTranslation()
  const title = t(`data:metric.${metric}`)
  const wide = useMediaQuery(WIDE)
  const body = (
    <>
      <TrafficKey />
      <SymbolKey drawn={drawn} airportsFailed={airportsFailed} />
      <div className={styles.layers}>{children}</div>
    </>
  )
  return (
    <LegendPanel title={title}>
      <Swap swapKey={metric} as="div" className={styles.key}>
        <MetricRamp metric={metric} scale={scale} />
      </Swap>
      {wide ? body : <Disclosure title={t("map:legend.layers")}>{body}</Disclosure>}
    </LegendPanel>
  )
}

function MetricRamp({
  metric,
  scale,
}: {
  readonly metric: MetricKey
  readonly scale: MetricScale
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const last = scale.bins.length - 1
  return (
    <ol className={styles.ramp}>
      {scale.hasZero ? (
        <li className={clsx(styles.bin, styles.zero)}>
          <span className={styles.step} data-step={1} aria-hidden="true" />
          <span className={styles.tick}>{formatThreshold(0, metric, f)}</span>
        </li>
      ) : null}
      {scale.bins.map((bin, index) => {
        const value = formatThreshold(bin.from, metric, f)
        const shown = index === 0 || index === last || index === Math.round(last / 2)
        return (
          <li key={bin.step} className={styles.bin}>
            <span className={styles.step} data-step={bin.step} aria-hidden="true" />
            <span className={styles.tick} data-quiet={!shown || undefined} aria-hidden="true">
              {value}
            </span>
            <span className="visually-hidden">{t("map:legend.from", { value })}</span>
          </li>
        )
      })}
    </ol>
  )
}

function SymbolKey({
  drawn,
  airportsFailed,
}: {
  readonly drawn: Readonly<Record<MapSymbol, boolean>>
  readonly airportsFailed: boolean
}) {
  const { t } = useTranslation()
  return (
    <ul className={styles.symbols} aria-label={t("map:legend.symbols")}>
      {SYMBOLS.map((symbol) => {
        const off = !drawn[symbol]
        const label =
          symbol === "airport" && airportsFailed ? "map:airports.failed" : SYMBOL_LABEL[symbol]
        return (
          <li key={symbol} className={styles.symbol} data-off={off || undefined}>
            <span className={styles.mark} data-symbol={symbol} aria-hidden="true" />
            <span>{t(label)}</span>
            {off ? <span className="visually-hidden">{t("map:legend.off")}</span> : null}
          </li>
        )
      })}
    </ul>
  )
}

interface LinkLayersProps {
  readonly selected: boolean
  readonly loading: boolean
  readonly failed: boolean
  readonly missing: number
  readonly modelCount: number
  readonly showModels: boolean
  readonly onModelsChange: (value: boolean) => void
  readonly onRetry: () => void
}

export function LinkLayers({
  selected,
  loading,
  failed,
  missing,
  modelCount,
  showModels,
  onModelsChange,
  onRetry,
}: LinkLayersProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const settled = !selected || failed || !loading
  const count = useLatched(selected && !failed ? modelCount : null, settled)
  const available = count !== null && count > 0
  const error = usePresence(selected && failed)
  const help = [
    t("map:connections.schematic"),
    modelCount > 0 ? t("map:connections.model") : "",
    missing > 0 ? t("map:connections.missing", { count: missing }) : "",
  ]
    .filter(Boolean)
    .join(" ")
  return (
    <>
      <div className={styles.row}>
        <Switch
          label={t("map:legend.models")}
          checked={available && showModels}
          disabled={!available}
          onChange={onModelsChange}
        />
        <span className={styles.count} data-stale={!settled || undefined}>
          <Swap swapKey={count ?? "idle"}>{count === null ? null : f.integer(count)}</Swap>
        </span>
        <LegendHelp content={help} />
      </div>
      {error.mounted ? (
        <div
          className={styles.reveal}
          data-state={error.state}
          onAnimationEnd={error.onAnimationEnd}
          role="status"
        >
          <p className={styles.note}>{t("map:connections.failed")}</p>
          <Button variant="ghost" size="compact" icon="retry" onClick={onRetry}>
            {t("common:action.retry")}
          </Button>
        </div>
      ) : null}
    </>
  )
}

function LegendHelp({ content }: { readonly content: string }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const anchor = useRef<HTMLButtonElement>(null)
  const id = useId()
  return (
    <>
      <Button
        ref={anchor}
        variant="ghost"
        size="compact"
        icon="info"
        aria-label={t("map:connections.details")}
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={() => setOpen((value) => !value)}
      >
        {null}
      </Button>
      <Popover
        id={id}
        open={open}
        onClose={() => setOpen(false)}
        anchorRef={anchor}
        side="top"
        align="end"
        label={t("map:connections.details")}
        focusOnOpen
        className={styles.help}
      >
        <p>{content}</p>
      </Popover>
    </>
  )
}
