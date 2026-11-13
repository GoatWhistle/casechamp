import { useEffect, useRef } from "react"
import { useTranslation } from "@/shared/i18n"
import { Button, Tooltip } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import styles from "./panel-dock.module.css"
import type { DockToggleState } from "./use-panel-dock"

export interface DockToggleProps {
  readonly dock: DockToggleState
}

function focusLost(): boolean {
  const active = document.activeElement
  if (active === null || active === document.body) return true
  return active instanceof HTMLElement && active.checkVisibility?.() === false
}

function focusLeftPanel(): boolean {
  return focusLost() || document.activeElement?.closest("[data-dock-slot]") != null
}

function panelFocusTarget(toggle: HTMLElement | null): HTMLElement | null {
  if (toggle?.checkVisibility?.()) return toggle
  return document.querySelector<HTMLElement>("[data-dock-slot] [data-sheet-focus]")
}

export function DockToggle({ dock }: DockToggleProps) {
  const { t } = useTranslation()
  const { docked: collapsed, collapse, expand: onExpand } = dock
  const launcher = useRef<HTMLButtonElement>(null)
  const toggle = useRef<HTMLButtonElement>(null)
  const previous = useRef(collapsed)

  useEffect(() => {
    if (previous.current === collapsed) return
    previous.current = collapsed
    if (collapsed) {
      if (focusLeftPanel()) launcher.current?.focus({ preventScroll: true })
      return
    }
    const frame = requestAnimationFrame(() => {
      if (focusLost()) panelFocusTarget(toggle.current)?.focus({ preventScroll: true })
    })
    return () => cancelAnimationFrame(frame)
  }, [collapsed])

  if (!collapsed)
    return (
      <Tooltip content={t("map:dock.collapse")} describe={false}>
        <Button
          ref={toggle}
          variant="secondary"
          icon="panel-close"
          className={styles.toggle}
          aria-label={t("map:dock.collapse")}
          onClick={() => collapse()}
        >
          {null}
        </Button>
      </Tooltip>
    )
  return (
    <Tooltip content={t("map:dock.expand")} describe={false}>
      <Button
        ref={launcher}
        className={styles.launcher}
        aria-label={t("map:dock.expand")}
        onClick={onExpand}
      >
        <BrandMark kind="symbol" tone="inverse" size="sm" rings={0} decorative />
      </Button>
    </Tooltip>
  )
}
