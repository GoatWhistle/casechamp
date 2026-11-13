import { useState } from "react"
import { useMunicipalAccess } from "@/entities/region"
import {
  clearMunicipalAccess,
  showMunicipalAccess,
  useMunicipalAccessView,
} from "@/shared/hooks/use-municipal-access-view"
import { type MessageKey, useTranslation } from "@/shared/i18n"
import { Button, ErrorState, Select, Skeleton, TextField } from "@/shared/ui"
import type { MunicipalNormative } from "../municipality-service-values"
import styles from "./municipal-access.module.css"
import { MunicipalAccessResults } from "./municipal-access-results"

export function MunicipalAccess({
  regionId,
  municipalityId,
  rows,
}: {
  readonly regionId: string
  readonly municipalityId: string
  readonly rows: readonly MunicipalNormative[]
}) {
  const { t } = useTranslation()
  const view = useMunicipalAccessView()
  const target = currentTarget(view, regionId, municipalityId)
  const [criterion, setCriterion] = useState(target?.criterion_id ?? "")
  const [threshold, setThreshold] = useState(target ? String(target.threshold) : "")
  const row = rows.find((item) => item.criterion_id === criterion)
  const query = useMunicipalAccess(target)
  const choose = (id: string) => {
    setCriterion(id)
    setThreshold(String(rows.find((item) => item.criterion_id === id)?.thresholds[0] ?? ""))
  }
  const value = Number(threshold.replace(",", "."))
  const valid = validThreshold(criterion, value)
  return (
    <section className={styles.content} aria-label={t("map:municipalAccess.title")}>
      <strong>{t("map:municipalAccess.title")}</strong>
      <Select
        label={t("map:municipalAccess.service")}
        value={criterion || null}
        onChange={choose}
        options={rows.map((item) => ({
          value: item.criterion_id,
          label: serviceLabel(item, t),
        }))}
      />
      <div className={styles.controls}>
        <TextField
          label={t(
            row?.unit === "metres" ? "map:municipalAccess.metres" : "map:municipalAccess.minutes",
          )}
          inputMode="decimal"
          value={threshold}
          onChange={(event) => setThreshold(event.target.value)}
        />
        <Button
          disabled={!valid}
          onClick={() =>
            showMunicipalAccess({
              region_id: regionId,
              municipality_id: municipalityId,
              criterion_id: criterion,
              threshold: value,
              deficit_only: true,
            })
          }
        >
          {t("map:municipalAccess.show")}
        </Button>
      </div>
      {target ? (
        <>
          <Button
            variant="ghost"
            onClick={() =>
              showMunicipalAccess({ ...target, deficit_only: !(target.deficit_only ?? true) })
            }
          >
            {t(filterLabel(target.deficit_only))}
          </Button>
          <Button variant="ghost" onClick={clearMunicipalAccess}>
            {t("map:municipalAccess.clear")}
          </Button>
          {query.isPending ? (
            <Skeleton lines={2} />
          ) : query.isError ? (
            <ErrorState
              title={t("map:municipalAccess.error")}
              onRetry={() => void query.refetch()}
            />
          ) : query.data ? (
            <MunicipalAccessResults data={query.data} selectedId={view.pointId} />
          ) : null}
        </>
      ) : null}
    </section>
  )
}

function currentTarget(
  view: ReturnType<typeof useMunicipalAccessView>,
  region: string,
  municipality: string,
) {
  return view.target?.region_id === region && view.target.municipality_id === municipality
    ? view.target
    : null
}

function validThreshold(criterion: string, value: number) {
  return Boolean(criterion) && Number.isFinite(value) && value > 0
}

function filterLabel(deficitOnly: boolean | undefined): MessageKey {
  return deficitOnly === false ? "map:municipalAccess.onlyDeficit" : "map:municipalAccess.allPoints"
}

function serviceLabel(row: MunicipalNormative, t: ReturnType<typeof useTranslation>["t"]): string {
  return row.criterion_id === "N01" || row.criterion_id === "N02"
    ? t("map:municipalAccess.medicalOption", { threshold: row.thresholds[0] })
    : t(`data:metric.normative_${row.criterion_id}` as MessageKey)
}
