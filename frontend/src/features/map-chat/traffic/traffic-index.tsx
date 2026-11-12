import { useState } from "react"
import {
  type TrafficAlternative,
  type TrafficJob,
  usefulTrafficAlternatives,
} from "@/shared/api/traffic"
import { showTrafficView } from "@/shared/hooks/use-traffic-view"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { DataTable, Icon, NoValue, Select } from "@/shared/ui"
import styles from "./traffic-index.module.css"

export function TrafficIndex({
  job,
  variant,
}: {
  readonly job: TrafficJob
  readonly variant: string
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [selected, setSelected] = useState("")
  const region = job.indices.find((item) => item.region === selected) ?? job.indices[0]
  if (!region) return <p>{t("traffic:indexUnavailable")}</p>
  const delta = (row: TrafficAlternative) =>
    row.indices?.find((item) => item.region === region.region)
  const ranked = usefulTrafficAlternatives(job, region.region).sort(
    (a, b) => (delta(b)?.delta ?? 0) - (delta(a)?.delta ?? 0),
  )
  return (
    <div className={styles.index}>
      {job.indices.length > 1 ? (
        <Select
          label={t("traffic:indexRegion")}
          hideLabel
          value={region.region}
          options={job.indices.map((item) => ({ value: item.region, label: item.region }))}
          onChange={setSelected}
        />
      ) : (
        <p className={styles.region}>{region.region}</p>
      )}
      <p className={styles.note}>
        {t("traffic:baselineIndex", { value: f.number(region.value, 2) })}
      </p>
      {ranked.length ? (
        <DataTable<TrafficAlternative>
          caption={t("traffic:comparison")}
          rows={ranked}
          rowKey={(row) => row.id}
          selectedKey={variant}
          onRowClick={(row) => showTrafficView(job, row.id, "project")}
          columns={[
            {
              key: "kind",
              header: t("traffic:project"),
              cell: (row) => (
                <span className={styles.project}>
                  <span>{t(`traffic:kind.${row.kind}`)}</span>
                  {row.road_names?.length ? (
                    <small>
                      {row.road_names.filter((name) => !/^\d{7,}$/.test(name)).join(", ")}
                    </small>
                  ) : null}
                </span>
              ),
            },
            {
              key: "minutes",
              header: t("traffic:localMinutes"),
              numeric: true,
              cell: (row) => (
                <TripTime
                  before={job.baseline?.mean_trip_minutes}
                  after={row.after.mean_trip_minutes}
                />
              ),
            },
            {
              key: "index",
              header: t("traffic:indexColumn"),
              numeric: true,
              cell: (row) => (
                <span className={styles.project}>
                  <span>{delta(row) ? f.number(delta(row)?.after ?? 0, 2) : <NoValue />}</span>
                  <small>
                    {Math.abs(delta(row)?.delta ?? 0) < 0.0001
                      ? t("traffic:unchanged")
                      : t("traffic:indexGain", { value: f.number(delta(row)?.delta ?? 0, 4) })}
                  </small>
                </span>
              ),
            },
          ]}
        />
      ) : (
        <p>{t("traffic:noImprovements")}</p>
      )}
    </div>
  )
}

function TripTime({
  before,
  after,
}: {
  readonly before?: number | null | undefined
  readonly after?: number | null | undefined
}) {
  const f = useFormatters()
  if (before == null || after == null) return <NoValue />
  return (
    <span className={styles.change}>
      <span>{f.number(before, 1)}</span>
      <Icon name="arrow-right" size="sm" />
      <strong>{f.number(after, 1)}</strong>
    </span>
  )
}
