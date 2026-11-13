import { useEffect, useRef } from "react"
import type { components } from "@/shared/api/schema.gen"
import { selectMunicipalAccessPoint } from "@/shared/hooks/use-municipal-access-view"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, HelpTip, Stat } from "@/shared/ui"
import { TransitJourney } from "../transit/transit-journey"
import styles from "./municipal-access.module.css"

export function MunicipalAccessResults({
  data,
  selectedId,
}: {
  readonly data: components["schemas"]["MunicipalAccessResponse"]
  readonly selectedId: string | null
}) {
  const detailRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (selectedId) detailRef.current?.scrollIntoView({ block: "nearest", inline: "nearest" })
  }, [selectedId])
  const { t } = useTranslation()
  const f = useFormatters()
  const cost = (value: number | null | undefined) =>
    value == null
      ? t("map:municipalCard.unavailable")
      : t(
          data.unit === "metres" ? "map:municipalAccess.distance" : "map:municipalAccess.duration",
          {
            value: f.number(value, 1),
          },
        )
  const selected = data.points.find((item) => item.row.id === selectedId)
  return (
    <div className={styles.content} aria-live="polite">
      <Stat
        layout="row"
        label={t("map:municipalAccess.deficit")}
        value={f.integer(data.deficit_points)}
        help={
          <HelpTip
            label={t("map:municipalAccess.deficit")}
            content={t("map:municipalAccess.countHelp", {
              total: data.reference_points,
              unreachable: data.unreachable_points,
              unresolved: data.unresolved_points,
            })}
          />
        }
      />
      <Stat
        layout="row"
        label={t("map:municipalAccess.periphery")}
        value={cost(data.p90)}
        help={
          <HelpTip
            label={t("map:municipalAccess.periphery")}
            content={t("map:municipalAccess.percentileHelp", {
              mean: cost(data.worst_decile_mean),
              count: data.measured_points,
            })}
          />
        }
      />
      {data.points.slice(0, 3).map(({ row }) => (
        <Button
          key={row.id}
          variant="ghost"
          aria-pressed={row.id === selectedId}
          onClick={() => selectMunicipalAccessPoint(row.id)}
        >
          <span className={styles.point}>
            <span>{row.name || row.id}</span>
            <span>
              {row.state === "unreachable"
                ? t("map:municipalAccess.noRoute")
                : cost(data.unit === "metres" ? row.distance_metres : row.minutes)}
            </span>
          </span>
        </Button>
      ))}
      {selected ? (
        <div ref={detailRef} className={styles.detail}>
          <strong>{selected.row.name || selected.row.id}</strong>
          <span>
            {cost(data.unit === "metres" ? selected.row.distance_metres : selected.row.minutes)}
          </span>
          <span>{selected.facility?.name || t("map:municipalAccess.noFacility")}</span>
          {selected.facility ? (
            <TransitJourney
              key={`${data.region_id}:${selected.row.id}:${selected.facility.id}`}
              regionId={data.region_id}
              originId={selected.row.id}
              facilityId={selected.facility.id}
            />
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
