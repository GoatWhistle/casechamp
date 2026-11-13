import type { AnimationEvent, ReactNode } from "react"
import { useTranslation } from "@/shared/i18n"
import { PanelResizer } from "@/shared/ui"
import styles from "./panel-dock.module.css"
import type { PanelDockState } from "./use-panel-dock"

export interface PanelDockProps {
  readonly dock: PanelDockState
  readonly children: ReactNode
}

export function PanelDock({ dock, children }: PanelDockProps) {
  const { t } = useTranslation()
  const { width, phase } = dock
  const settle = (event: AnimationEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) dock.settle()
  }
  return (
    <>
      <div
        className={styles.slot}
        data-phase={phase}
        inert={phase === "closed"}
        onAnimationEnd={settle}
      >
        {children}
      </div>
      {phase === "open" ? (
        <PanelResizer
          className={styles.resizer}
          width={width.width}
          min={width.min}
          max={width.max}
          label={t("map:panelResize")}
          onPreview={width.preview}
          onCommit={width.commit}
          onReset={width.reset}
          collapseBelow={dock.collapseBelow}
          onCollapse={() => dock.collapse(true)}
        />
      ) : null}
    </>
  )
}
