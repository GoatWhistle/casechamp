import { useState } from "react"
import { useTransitJourney } from "@/entities/region"
import { showTransitJourney } from "@/shared/hooks/use-transit-view"
import { useTranslation } from "@/shared/i18n"
import { Button, Icon, Skeleton, TextField } from "@/shared/ui"
import styles from "./transit-journey.module.css"
import { TransitResult } from "./transit-result"

export function TransitJourney({
  regionId,
  originId,
  facilityId,
}: {
  readonly regionId: string
  readonly originId: string
  readonly facilityId: string
}) {
  const { t } = useTranslation()
  const [time, setTime] = useState("08:00")
  const journey = useTransitJourney(regionId)
  const departure = clockSeconds(time)
  return (
    <section className={styles.content} aria-label={t("map:transit.title")}>
      <div className={styles.controls}>
        <TextField
          label={t("map:transit.departure")}
          value={time}
          maxLength={5}
          disabled={journey.isPending}
          onChange={(event) => {
            setTime(event.target.value)
            journey.reset()
            showTransitJourney(null)
          }}
        />
        <Button
          variant="secondary"
          disabled={departure === null || journey.isPending}
          aria-busy={journey.isPending}
          onClick={() => {
            if (departure !== null)
              journey.mutate(
                {
                  origin_id: originId,
                  facility_id: facilityId,
                  departure_seconds: departure,
                },
                { onSuccess: (data) => showTransitJourney(data.map_target) },
              )
          }}
        >
          <Icon name="bus" />
          {t("map:transit.title")}
        </Button>
      </div>
      {journey.isPending ? <Skeleton lines={2} /> : null}
      {journey.isError ? <p role="alert">{t("map:transit.error")}</p> : null}
      {journey.data ? <TransitResult data={journey.data} /> : null}
    </section>
  )
}

function clockSeconds(value: string): number | null {
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) return null
  const [hours, minutes] = value.split(":").map(Number)
  return (hours ?? 0) * 3600 + (minutes ?? 0) * 60
}
