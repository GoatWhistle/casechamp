import type { ReactNode } from "react"
import type { MapControls } from "@/entities/region"
import type { MessageKey } from "@/shared/i18n"
import { useTranslation } from "@/shared/i18n"
import { Button, type IconName, Tooltip } from "@/shared/ui"
import styles from "./map-explorer.module.css"

export interface MapZoomProps {
  readonly controls: MapControls
  readonly onReset: () => void
  readonly dock?: ReactNode
}

interface ZoomAction {
  readonly label: MessageKey
  readonly icon: IconName
  readonly run: (instant?: boolean) => void
}

export function MapZoom({ controls, onReset, dock }: MapZoomProps) {
  const { t } = useTranslation()
  const actions: readonly ZoomAction[] = [
    { label: "map:zoomIn", icon: "plus", run: controls.zoomIn },
    { label: "map:zoomOut", icon: "minus", run: controls.zoomOut },
    {
      label: "map:reset",
      icon: "locate",
      run: (instant) => {
        controls.reset(instant)
        onReset()
      },
    },
  ]
  return (
    <div className={styles.controls}>
      {dock}
      <div className={styles.zoom}>
        {actions.map((action) => (
          <Tooltip key={action.icon} content={t(action.label)} side="bottom" describe={false}>
            <Button
              variant="secondary"
              size="compact"
              icon={action.icon}
              onClick={(event) => action.run(event.detail === 0)}
              aria-label={t(action.label)}
            >
              {null}
            </Button>
          </Tooltip>
        ))}
      </div>
    </div>
  )
}
