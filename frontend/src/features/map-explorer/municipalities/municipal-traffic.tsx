import { useState } from "react"
import { useMunicipalScenario, useMunicipalTraffic } from "@/entities/region"
import { isTrafficJob } from "@/shared/api/traffic"
import { showTrafficView } from "@/shared/hooks/use-traffic-view"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import { Button, HelpTip, Icon, Select, Skeleton } from "@/shared/ui"
import { MunicipalSegmentSelection } from "./municipal-segment-actions"
import styles from "./municipal-traffic.module.css"
import { MunicipalTrafficResult } from "./municipal-traffic-result"

export function MunicipalTraffic({
  regionId,
  municipalityId,
}: {
  readonly regionId: string
  readonly municipalityId: string
}) {
  const query = useMunicipalTraffic(regionId, municipalityId)
  const submit = useMunicipalScenario()
  const [selected, setSelected] = useState<string | null>(null)
  const { t } = useTranslation()
  const selectedRoad = query.data?.corridors.find((road) => String(road.way_id) === selected)
  const capacityAllowed = selectedRoad?.capacity_eligible !== false
  const start = (kind: "capacity" | "closure") => {
    if (!query.data || !selected) return
    submit.mutate({
      baseline_id: query.data.baseline_id,
      region_id: regionId,
      municipality_id: municipalityId,
      kind,
      way_ids: [Number(selected)],
    })
  }
  return (
    <section className={styles.content} aria-label={t("map:municipalTraffic.title")}>
      <p className={styles.heading}>
        <Icon name="route" />
        <strong>{t("map:municipalTraffic.title")}</strong>
        <HelpTip
          content={t("map:municipalTraffic.assumption")}
          label={t("map:municipalCard.metricHelp", { name: t("map:municipalTraffic.title") })}
        />
      </p>
      {query.isPending ? (
        <Skeleton lines={3} />
      ) : query.isError ? (
        <>
          <p>{t("map:municipalTraffic.unavailable")}</p>
          <Button variant="ghost" onClick={() => void query.refetch()}>
            {t("map:municipalTraffic.retry")}
          </Button>
        </>
      ) : (
        <>
          <Button
            variant="secondary"
            onClick={() => {
              if (isTrafficJob(query.data.view))
                showTrafficView(query.data.view, "baseline", "before")
            }}
          >
            {t("map:municipalTraffic.showLoad")}
          </Button>
          <p>{t("map:municipalTraffic.pickSegment")}</p>
          <MunicipalSegmentSelection
            baseline={query.data}
            regionId={regionId}
            municipalityId={municipalityId}
            pending={submit.isPending}
            onSubmit={submit.mutate}
          />
          {query.data.corridors
            .filter((road) => road.capacity_eligible !== false)
            .slice(0, 3)
            .map((road) => (
              <Button
                key={road.way_id}
                variant={selected === String(road.way_id) ? "secondary" : "ghost"}
                wrap
                onClick={() => setSelected(String(road.way_id))}
              >
                {t(
                  road.name
                    ? "map:municipalTraffic.namedCorridor"
                    : "map:municipalTraffic.corridor",
                  { name: road.name, id: road.way_id, ratio: road.peak_ratio },
                )}
              </Button>
            ))}
          <Select
            label={t("map:municipalTraffic.select")}
            value={selected}
            onChange={setSelected}
            options={query.data.corridors.map((road) => ({
              value: String(road.way_id),
              label: t(
                road.name ? "map:municipalTraffic.namedCorridor" : "map:municipalTraffic.corridor",
                {
                  name: road.name,
                  id: road.way_id,
                  ratio: road.peak_ratio,
                },
              ),
            }))}
          />
          <div className={styles.actions}>
            <Button
              disabled={!selected || !capacityAllowed || submit.isPending}
              onClick={() => start("capacity")}
            >
              {t("map:municipalTraffic.capacity")}
            </Button>
            {!capacityAllowed ? (
              <HelpTip
                label={t("map:municipalTraffic.capacityUnavailable")}
                content={t(capacityReason(selectedRoad?.capacity_reason))}
              />
            ) : null}
            <Button
              variant="secondary"
              disabled={!selected || submit.isPending}
              onClick={() => start("closure")}
            >
              {t("map:municipalTraffic.closure")}
            </Button>
          </div>
          {submit.isError ? <p role="alert">{t("map:municipalTraffic.failed")}</p> : null}
          {submit.data ? (
            <MunicipalTrafficResult key={submit.data.id} identifier={submit.data.id} />
          ) : null}
        </>
      )}
    </section>
  )
}

const CAPACITY_REASONS: Readonly<Record<string, MessageKey>> = {
  disconnected_segments: "map:municipalTraffic.disconnectedCapacity",
  shared_lane: "map:municipalTraffic.sharedCapacity",
  no_assigned_demand: "map:municipalTraffic.noDemandCapacity",
}

function capacityReason(reason: string | null | undefined): MessageKey {
  return CAPACITY_REASONS[reason ?? ""] ?? "map:municipalTraffic.capacityUnavailable"
}
