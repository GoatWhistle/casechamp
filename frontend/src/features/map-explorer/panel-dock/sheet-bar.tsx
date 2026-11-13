import { useTranslation } from "@/shared/i18n"
import { Button, Tooltip } from "@/shared/ui"
import styles from "./sheet-bar.module.css"
import type { PanelDockState } from "./use-panel-dock"

export interface SheetBarProps {
  readonly dock: PanelDockState
}

export function SheetBar({ dock }: SheetBarProps) {
  const { t } = useTranslation()
  const full = dock.sheet === "full"
  const size = t(full ? "map:dock.shrink" : "map:dock.fill")
  const hide = t("map:dock.collapse")
  return (
    <div className={styles.bar}>
      <Tooltip content={size} describe={false}>
        <Button
          variant="ghost"
          icon={full ? "shrink" : "expand"}
          aria-label={size}
          data-sheet-focus
          onClick={(event) => dock.toggleSheet(event.detail === 0)}
        >
          {null}
        </Button>
      </Tooltip>
      <Tooltip content={hide} describe={false}>
        <Button
          variant="ghost"
          icon="chevron-down"
          aria-label={hide}
          onClick={(event) => dock.collapse(event.detail === 0)}
        >
          {null}
        </Button>
      </Tooltip>
    </div>
  )
}
