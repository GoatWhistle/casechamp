import { useState } from "react"
import {
  useNormativeAssessment,
  useNormativeCriteria,
  useNormativeFacilities,
} from "@/entities/normative"
import { useErrorText, useFormatters, useTranslation } from "@/shared/i18n"
import {
  Banner,
  Button,
  ButtonLink,
  Card,
  EmptyState,
  ErrorState,
  Select,
  Skeleton,
  TextField,
} from "@/shared/ui"
import styles from "./normative-explorer.module.css"
import { NormativeFacilities } from "./normative-facilities"
import { NormativeResults } from "./normative-results"

export function NormativeExplorer() {
  const { t } = useTranslation()
  const f = useFormatters()
  const catalog = useNormativeCriteria()
  const [id, setId] = useState("N05")
  const [closure, setClosure] = useState("")
  const facilities = useNormativeFacilities(id)
  const assessment = useNormativeAssessment()
  const criterion = catalog.data?.find((item) => item.id === id)
  const closed =
    closure.trim() === "" ? [] : closure.split(",").map((value) => Number(value.trim()))
  const invalid =
    closed.length > 20 || closed.some((value) => !Number.isSafeInteger(value) || value <= 0)
  if (catalog.isError)
    return <ErrorState title={t("normative:loadError")} onRetry={() => void catalog.refetch()} />
  if (!catalog.data || !criterion) return <Skeleton lines={8} />
  const ready = criterion.mode === "car" && (facilities.data?.length ?? 0) > 0
  const result = assessment.data?.criterion.id === id ? assessment.data : undefined
  return (
    <div className={styles.workspace}>
      <aside className={styles.controls}>
        <Select
          label={t("normative:criterion")}
          value={id}
          onChange={(next) => {
            setId(next)
            assessment.reset()
          }}
          options={catalog.data.map((item) => ({
            value: item.id,
            label: t(`normative:criteria.${item.id as "N05"}`),
          }))}
        />
        <Card title={t("normative:act", { act: criterion.act, clause: criterion.clause })}>
          <p>{t("normative:edition", { date: f.date(criterion.edition_date) })}</p>
          <ButtonLink to={criterion.source_url} icon="external" variant="ghost">
            {t("normative:source")}
          </ButtonLink>
        </Card>
        <Banner
          tone="warning"
          title={t("normative:published")}
          description={t("normative:caution")}
        />
        <TextField
          label={t("normative:closure")}
          value={closure}
          onChange={(event) => setClosure(event.target.value)}
          hint={t("normative:closureHint")}
          error={invalid ? t("normative:closureError") : undefined}
        />
        <Button
          icon="scenario"
          disabled={!ready || invalid || assessment.isPending}
          pending={assessment.isPending}
          onClick={() => assessment.mutate({ criterion_id: id, closed_way_ids: closed })}
        >
          {t("normative:calculate")}
        </Button>
        <ButtonLink to="/" icon="map" variant="ghost">
          {t("normative:openMap")}
        </ButtonLink>
        {facilities.isError ? (
          <ErrorState title={t("normative:loadError")} onRetry={() => void facilities.refetch()} />
        ) : null}
        {facilities.data ? (
          <NormativeFacilities facilities={facilities.data} />
        ) : (
          <Skeleton lines={3} />
        )}
      </aside>
      <section
        className={styles.content}
        aria-label={t("normative:resultRegion")}
        aria-busy={assessment.isPending}
      >
        <NormativeOutput
          ready={ready}
          mode={criterion.mode}
          assessment={assessment}
          result={result}
          onRetry={() => assessment.mutate({ criterion_id: id, closed_way_ids: closed })}
        />
      </section>
    </div>
  )
}

function NormativeOutput({
  ready,
  mode,
  assessment,
  result,
  onRetry,
}: {
  readonly ready: boolean
  readonly mode: string
  readonly assessment: ReturnType<typeof useNormativeAssessment>
  readonly result: ReturnType<typeof useNormativeAssessment>["data"]
  readonly onRetry: () => void
}) {
  const { t } = useTranslation()
  const errorText = useErrorText()
  return (
    <>
      {" "}
      {!ready ? (
        <EmptyState
          icon="info"
          title={t(mode === "car" ? "normative:emptyFacilities" : "normative:unsupported")}
        />
      ) : assessment.isError ? (
        <ErrorState
          title={t("normative:calculationError")}
          description={errorText(assessment.error)}
          onRetry={onRetry}
        />
      ) : result ? (
        <NormativeResults result={result} />
      ) : assessment.isPending ? (
        <Skeleton lines={12} />
      ) : (
        <EmptyState icon="scenario" title={t("normative:waiting")} />
      )}
    </>
  )
}
