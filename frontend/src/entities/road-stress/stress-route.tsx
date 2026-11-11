import { showStressView, useStressView } from "@/shared/hooks/use-stress-view"
import { useTranslation } from "@/shared/i18n"
import { Button, Disclosure } from "@/shared/ui"
import styles from "./stress-card.module.css"
import { StressPlace } from "./stress-place"
import type { useStressTest } from "./use-stress-test"
export function StressRoutePanel({
  id,
  origin,
  destination,
  setOrigin,
  setDestination,
  state,
}: {
  readonly id: string | null
  readonly origin: string
  readonly destination: string
  readonly setOrigin: (id: string) => void
  readonly setDestination: (id: string) => void
  readonly state: ReturnType<typeof useStressTest>
}) {
  const { t } = useTranslation()
  const view = useStressView()
  return (
    <Disclosure title={t("stress:route")}>
      {view.jobId === id && view.selected?.point.id === origin ? (
        <p>{t("stress:selectedOrigin", { name: view.selected.point.name })}</p>
      ) : null}
      <StressPlace key={`${id}-origin`} label={t("stress:origin")} onSelect={setOrigin} />
      <StressPlace
        key={`${id}-destination`}
        label={t("stress:destination")}
        onSelect={setDestination}
      />
      <Button
        icon="map"
        disabled={!origin || !destination || state.route.isPending}
        onClick={() =>
          state.route.mutate(
            { origin, destination },
            { onSuccess: (route) => showStressView({ jobId: id, impacts: [], route }) },
          )
        }
      >
        {t("stress:compare")}
      </Button>
      {state.route.data ? (
        <div className={styles.comparison}>
          {(["before", "after"] as const).map((key) => (
            <p key={key}>
              <strong>{t(`stress:${key}`)}</strong>{" "}
              {state.route.data?.[key].status === "reachable"
                ? t("stress:travel", {
                    minutes: Math.round((state.route.data[key].hours ?? 0) * 60),
                    km: Math.round(state.route.data[key].km ?? 0),
                  })
                : t("stress:noPath")}
            </p>
          ))}
        </div>
      ) : null}
    </Disclosure>
  )
}
