import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import styles from "./stress-card.module.css"
export function StressActions({
  selectedWays,
  id,
  pending,
  launch,
}: {
  readonly selectedWays: readonly number[]
  readonly id: string | null
  readonly pending: boolean
  readonly launch: (parent: boolean) => void
}) {
  const { t } = useTranslation()
  return (
    <>
      {selectedWays.length ? (
        <div className={styles.actions}>
          <Button icon="route" disabled={pending} onClick={() => launch(false)}>
            {t("stress:run", { count: selectedWays.length })}
          </Button>
          {id ? (
            <Button icon="plus" variant="secondary" disabled={pending} onClick={() => launch(true)}>
              {t("stress:add")}
            </Button>
          ) : null}
        </div>
      ) : !id ? (
        <p>{t("stress:select")}</p>
      ) : null}
    </>
  )
}
