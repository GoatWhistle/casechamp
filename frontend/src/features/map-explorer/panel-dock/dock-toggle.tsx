import { useTranslation } from "@/shared/i18n"
import { Button, Tooltip } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import styles from "./panel-dock.module.css"
import type { DockToggleState } from "./use-panel-dock"

export interface DockToggleProps {
  readonly dock: DockToggleState
}

export function DockToggle({ dock }: DockToggleProps) {
  const { t } = useTranslation()
  const { docked: collapsed, collapse, expand: onExpand } = dock
  if (!collapsed)
    return (
      <Tooltip content={t("map:dock.collapse")} describe={false}>
        <Button
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
      <Button className={styles.launcher} aria-label={t("map:dock.expand")} onClick={onExpand}>
        <BrandMark kind="symbol" tone="inverse" size="sm" rings={0} decorative />
      </Button>
    </Tooltip>
  )
}
