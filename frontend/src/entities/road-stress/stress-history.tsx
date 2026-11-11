import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"
import { useTranslation } from "@/shared/i18n"
import { Button, Disclosure } from "@/shared/ui"
import styles from "./stress-card.module.css"

export function StressHistory({
  id,
  select,
}: {
  readonly id: string | null
  readonly select: (id: string) => void
}) {
  const { t } = useTranslation()
  const history = useQuery({
    queryKey: ["road-stress-history", id],
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/road-stress-tests", { signal })),
  })
  return (
    <Disclosure title={t("stress:history")}>
      <div className={styles.regions}>
        {(history.data ?? []).slice(0, 20).map((job) => (
          <Button
            key={job.id}
            icon="list"
            variant={id === job.id ? "primary" : "ghost"}
            onClick={() => select(job.id)}
          >
            {t("stress:historyItem", { id: job.id.slice(0, 6), ways: job.way_ids.length })}
          </Button>
        ))}
      </div>
    </Disclosure>
  )
}
