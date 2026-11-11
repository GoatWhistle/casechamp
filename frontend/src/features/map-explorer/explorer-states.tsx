import { useTranslation } from "@/shared/i18n"
import { ErrorState } from "@/shared/ui"
import { Isolines } from "@/shared/ui/brand"
import styles from "./map-explorer.module.css"

interface PendingProps {
  readonly failed: boolean
  readonly onRetry: () => void
}

function MapLoading() {
  const { t } = useTranslation()
  return (
    <div className={styles.mapLoading} role="status">
      <Isolines rings={3} motion="pulse" className={styles.loadingRings} />
      <span className="visually-hidden">{t("common:state.loading")}</span>
    </div>
  )
}

export function MapPending({ failed, onRetry }: PendingProps) {
  const { t } = useTranslation()
  if (!failed) return <MapLoading />
  return (
    <div className={styles.mapLoading}>
      <ErrorState title={t("errors:kind.server")} onRetry={onRetry} />
    </div>
  )
}
