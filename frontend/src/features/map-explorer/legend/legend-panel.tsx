import {
  type CSSProperties,
  type MouseEvent,
  type ReactNode,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react"
import { COMPACT_LAYOUT, usePanelWidth } from "@/shared/hooks"
import { useTranslation } from "@/shared/i18n"
import { usePresence } from "@/shared/motion"
import { Button, PanelResizer, ScrollArea } from "@/shared/ui"
import styles from "./legend-panel.module.css"
import { useLegendResize } from "./use-legend-resize"

const COLLAPSED_KEY = "plexus.map-legend-collapsed"
const WIDTH_KEY = "plexus.map-legend-width"

function initiallyOpen() {
  try {
    const stored = localStorage.getItem(COLLAPSED_KEY)
    return globalThis.matchMedia?.(COMPACT_LAYOUT).matches ? stored === "false" : stored !== "true"
  } catch {
    return true
  }
}

export interface LegendPanelProps {
  readonly title: string
  readonly children: ReactNode
}

export function LegendPanel({ title, children }: LegendPanelProps) {
  const { t } = useTranslation()
  const id = useId()
  const resizeHintId = `${id}-resize-hint`
  const host = useRef<HTMLDivElement>(null)
  const panel = useRef<HTMLElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)
  const collapse = useRef<HTMLButtonElement>(null)
  const restoreFocus = useRef(false)
  const [open, setOpen] = useState(initiallyOpen)
  const [instant, setInstant] = useState(false)
  const presence = usePresence(open, "--dur-fast-exit", instant)
  const size = usePanelWidth(host, WIDTH_KEY, {
    minToken: "--legend-width",
    baseToken: "--legend-default-width",
    maxToken: "--legend-max-width",
    maxShare: 1,
  })
  const resize = useLegendResize(panel, size)

  const toggle = (event: MouseEvent<HTMLButtonElement>) => {
    restoreFocus.current = true
    setInstant(event.detail === 0)
    setOpen(!open)
    try {
      localStorage.setItem(COLLAPSED_KEY, String(open))
    } catch {
      return
    }
  }

  useLayoutEffect(() => {
    if (!restoreFocus.current) return
    restoreFocus.current = false
    const target = open ? collapse.current : trigger.current
    target?.focus({ preventScroll: true })
  }, [open])

  return (
    <div
      ref={host}
      className={styles.host}
      style={{ "--panel-committed": size.width } as CSSProperties}
      data-instant={instant || undefined}
    >
      {!open ? (
        <Button
          ref={trigger}
          className={styles.launcher}
          variant="secondary"
          icon="layers"
          aria-label={t("map:legend.open")}
          aria-expanded={false}
          aria-controls={presence.mounted ? id : undefined}
          onClick={toggle}
        >
          {null}
        </Button>
      ) : null}
      {presence.mounted ? (
        <figure
          ref={panel}
          id={id}
          className={styles.panel}
          style={{ blockSize: resize.height }}
          aria-label={title}
          inert={!open}
          data-state={presence.state}
          onTransitionEnd={presence.onTransitionEnd}
        >
          <figcaption className={styles.header}>
            <span className={styles.title}>{title}</span>
            <Button
              ref={collapse}
              variant="ghost"
              size="compact"
              icon="minus"
              aria-label={t("map:legend.collapse")}
              aria-expanded={open}
              aria-controls={id}
              onClick={toggle}
            >
              {null}
            </Button>
          </figcaption>
          <ScrollArea className={styles.body}>{children}</ScrollArea>
          <PanelResizer
            className={styles.resizer}
            edge="end"
            width={size.width}
            min={size.min}
            max={size.max}
            label={t("map:legend.resize")}
            controls={id}
            onPreview={size.preview}
            onCommit={size.commit}
            onReset={size.reset}
          />
          <Button
            className={styles.corner}
            variant="ghost"
            aria-label={t("map:legend.resizeBoth")}
            aria-controls={id}
            aria-describedby={resizeHintId}
            {...resize.handlers}
          >
            {null}
          </Button>
          <span id={resizeHintId} hidden>
            {t("map:legend.resizeHint")}
          </span>
        </figure>
      ) : null}
    </div>
  )
}
