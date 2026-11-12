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
  const [selected, setSelected] = useState("")
  const region = job.indices.find((item) => item.region === selected) ?? job.indices[0]
  const objective = job.scope.objective ?? "connectivity"
  const targeted = objective !== "connectivity"
  if (!region && !targeted) return <p>{t("traffic:indexUnavailable")}</p>
  const delta = (row: TrafficAlternative) =>
    row.indices?.find((item) => item.region === region?.region)
  const ranked = usefulTrafficAlternatives(job, region?.region).sort((a, b) =>
    targeted
      ? (b.objective_gain ?? 0) - (a.objective_gain ?? 0)
      : (delta(b)?.delta ?? 0) - (delta(a)?.delta ?? 0),
  )
  return (
    <div className={styles.index}>
      <RegionHeading job={job} region={region} onChange={setSelected} />
      {ranked.length ? (
        <DataTable<TrafficAlternative>
          caption={t(targeted ? "traffic:objectiveComparison" : "traffic:comparison")}
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
              header: t(
                objective === "transit"
                  ? "traffic:transitMinutes"
                  : objective === "congestion"
                    ? "traffic:congestionMinutes"
                    : "traffic:localMinutes",
              ),
              numeric: true,
              cell: (row) => <TrafficTime row={row} job={job} targeted={targeted} />,
            },
            ...(region
              ? [
                  {
                    key: "index",
                    header: t("traffic:indexColumn"),
                    numeric: true,
                    cell: (row: TrafficAlternative) => <IndexValue delta={delta(row)} />,
                  },
                ]
              : []),
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

function objectiveMinutes(value: number | null | undefined, unit: string | undefined) {
  if (value == null || !Number.isFinite(value)) return null
  return unit === "hours" || unit === "vehicle_hours" ? value * 60 : null
}

function TrafficTime({
  row,
  job,
  targeted,
}: {
  readonly row: TrafficAlternative
  readonly job: TrafficJob
  readonly targeted: boolean
}) {
  const { t } = useTranslation()
  return (
    <span className={styles.project}>
      <TripTime
        before={
          targeted
            ? objectiveMinutes(row.objective_before, row.objective_unit)
            : job.baseline?.mean_trip_minutes
        }
        after={
          targeted
            ? objectiveMinutes(row.objective_after, row.objective_unit)
            : row.after.mean_trip_minutes
        }
      />
      {(row.overload_increase ?? 0) > 0 ? (
        <small>{t("traffic:overloadIncrease", { count: row.overload_increase ?? 0 })}</small>
      ) : null}
    </span>
  )
}

function IndexValue({
  delta,
}: {
  readonly delta: NonNullable<TrafficAlternative["indices"]>[number] | undefined
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!delta) return <NoValue />
  return (
    <span className={styles.project}>
      <span>{f.number(delta.after, 2)}</span>
      <small>
        {Math.abs(delta.delta) < 0.0001
          ? t("traffic:unchanged")
          : t(delta.delta < 0 ? "traffic:indexLoss" : "traffic:indexGain", {
              value: f.number(delta.delta, 4),
            })}
      </small>
    </span>
  )
}

function RegionHeading({
  job,
  region,
  onChange,
}: {
  readonly job: TrafficJob
  readonly region: TrafficJob["indices"][number] | undefined
  readonly onChange: (value: string) => void
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!region) return null
  return (
    <>
      {job.indices.length > 1 ? (
        <Select
          label={t("traffic:indexRegion")}
          hideLabel
          value={region.region}
          options={job.indices.map((item) => ({ value: item.region, label: item.region }))}
          onChange={onChange}
        />
      ) : (
        <p className={styles.region}>{region.region}</p>
      )}
      <p className={styles.note}>
        {t("traffic:baselineIndex", { value: f.number(region.value, 2) })}
      </p>
    </>
  )
}
