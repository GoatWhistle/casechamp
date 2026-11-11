import { useQuery } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import type { ChatEntry } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import { api, unwrap } from "@/shared/api/client"
import { showStressView, updateStressGeometry } from "@/shared/hooks/use-stress-view"
import { useTranslation } from "@/shared/i18n"
import { Button } from "@/shared/ui"
import styles from "./chat-result-map.module.css"

export function ChatResultMap({
  message,
  onCalculation,
  autoFocus,
}: {
  readonly message: ChatEntry
  readonly onCalculation: CalculationHandler | undefined
  readonly autoFocus: boolean
}) {
  const { t } = useTranslation()
  const calculation = message.calculations?.[0]
  const stress = message.stressTests?.[0]
  const geometry = useQuery({
    queryKey: ["road-stress-geometry", stress?.id],
    enabled: Boolean(stress),
    staleTime: Infinity,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}/geometry", {
          signal,
          params: { path: { job_id: stress?.id ?? "" } },
        }),
      ),
  })
  const shown = useRef(false)
  useEffect(() => {
    if (stress && geometry.data) updateStressGeometry(stress.id, geometry.data.lines)
  }, [stress, geometry.data])
  useEffect(() => {
    if (shown.current || !autoFocus || !calculation || !onCalculation || stress) return
    shown.current = true
    onCalculation(calculation)
  }, [autoFocus, calculation, onCalculation, stress])
  const show = (instant: boolean) => {
    if (stress)
      showStressView({
        showPoints: false,
        jobId: stress.id,
        impacts: [],
        route: message.stressRoutes?.[stress.id] ?? null,
        closed: geometry.data?.lines ?? [],
        regions: stress.regions ?? [],
      })
    else if (calculation) onCalculation?.(calculation, instant)
  }
  const target = calculation?.corridor.road_ref || calculation?.corridor.origin
  const label = target ? t("chat:calculationRun.mapTarget", { target }) : t("chat:calculation.show")
  return (
    <div className={styles.map}>
      <Button
        icon="map"
        size="compact"
        className={styles.action}
        aria-label={label}
        title={t("chat:calculationRun.mapHint")}
        variant="ghost"
        disabled={stress ? !geometry.data?.lines.length : !calculation || !onCalculation}
        onClick={(event) => show(event.detail === 0)}
      >
        {stress && geometry.isPending ? t("chat:calculationRun.waitingGeometry") : label}
      </Button>
      {geometry.isError ? (
        <Button size="compact" variant="ghost" icon="retry" onClick={() => void geometry.refetch()}>
          {t("chat:retry")}
        </Button>
      ) : null}
    </div>
  )
}
