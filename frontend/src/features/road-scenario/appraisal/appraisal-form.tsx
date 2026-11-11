import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { api, unwrap } from "@/shared/api/client"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, Disclosure, Switch, TextField } from "@/shared/ui"
import styles from "./appraisal-form.module.css"
import { AppraisalNumber } from "./appraisal-number"
import {
  emptyFreight,
  emptyPassenger,
  emptyProject,
  type Project,
  projectReady,
} from "./appraisal-state"
import { FreightEditor } from "./freight-editor"
import { PassengerEditor } from "./passenger-editor"

const costs = [
  "capital_cost_rub",
  "annual_operating_cost_rub",
  "horizon_years",
  "price_year",
] as const

export function AppraisalForm({
  value,
  regionId,
  onChange,
}: {
  readonly value: Project | null
  readonly regionId: string | null
  readonly onChange: (value: Project | null) => void
}) {
  const { t } = useTranslation()
  const [passengerKeys, setPassengerKeys] = useState(() =>
    (value?.passengers ?? []).map(() => crypto.randomUUID()),
  )
  const [freightKeys, setFreightKeys] = useState(() =>
    (value?.freight ?? []).map(() => crypto.randomUUID()),
  )
  const markets = useQuery({
    queryKey: ["graph-markets"],
    enabled: value !== null,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/road-graph/markets", { signal })),
  })
  return (
    <div className={styles.editor}>
      <Switch
        label={t("appraisal:enable")}
        checked={value !== null}
        onChange={(enabled) => {
          setPassengerKeys([])
          setFreightKeys([])
          onChange(enabled ? emptyProject() : null)
        }}
      />
      {value ? (
        <>
          <p>{t("appraisal:scope")}</p>
          {!regionId ? <Banner tone="info" title={t("graph:pickRegion")} /> : null}
          {markets.isError ? (
            <Banner
              tone="danger"
              title={t("appraisal:marketError")}
              action={
                <Button icon="retry" onClick={() => void markets.refetch()}>
                  {t("common:action.retry")}
                </Button>
              }
            />
          ) : null}
          {value.passengers.map((passenger, index) => (
            <Disclosure
              key={passengerKeys[index]}
              title={t("appraisal:passengerRow", { count: index + 1 })}
              defaultOpen
            >
              <div className={styles.fields}>
                <PassengerEditor
                  value={passenger}
                  markets={markets.data ?? []}
                  regionId={regionId}
                  onChange={(next) =>
                    onChange({
                      ...value,
                      passengers: value.passengers.map((p, i) => (i === index ? next : p)),
                    })
                  }
                  onRemove={() => {
                    setPassengerKeys((keys) => keys.filter((_, i) => i !== index))
                    onChange({
                      ...value,
                      passengers: value.passengers.filter((_, i) => i !== index),
                    })
                  }}
                />
              </div>
            </Disclosure>
          ))}
          <Button
            icon="plus"
            variant="secondary"
            disabled={markets.isPending || !regionId}
            onClick={() => {
              setPassengerKeys((keys) => [...keys, crypto.randomUUID()])
              onChange({ ...value, passengers: [...value.passengers, emptyPassenger()] })
            }}
          >
            {t("appraisal:addPassenger")}
          </Button>
          {(value.freight ?? []).map((flow, index) => (
            <Disclosure
              key={freightKeys[index]}
              title={t("appraisal:freightRow", { count: index + 1 })}
              defaultOpen
            >
              <div className={styles.fields}>
                <FreightEditor
                  value={flow}
                  onChange={(next) =>
                    onChange({
                      ...value,
                      freight: (value.freight ?? []).map((f, i) => (i === index ? next : f)),
                    })
                  }
                  onRemove={() => {
                    setFreightKeys((keys) => keys.filter((_, i) => i !== index))
                    onChange({
                      ...value,
                      freight: (value.freight ?? []).filter((_, i) => i !== index),
                    })
                  }}
                />
              </div>
            </Disclosure>
          ))}
          <Button
            icon="plus"
            variant="secondary"
            onClick={() => {
              setFreightKeys((keys) => [...keys, crypto.randomUUID()])
              onChange({ ...value, freight: [...(value.freight ?? []), emptyFreight()] })
            }}
          >
            {t("appraisal:addFreight")}
          </Button>
          <Disclosure title={t("appraisal:costs")} defaultOpen>
            <div className={styles.fields}>
              {costs.map((key) => (
                <AppraisalNumber
                  key={key}
                  label={t(`appraisal:costFields.${key}`)}
                  value={value[key]}
                  onChange={(number) => onChange({ ...value, [key]: number })}
                />
              ))}
              <AppraisalNumber
                label={t("appraisal:discount")}
                value={value.discount_rate * 100}
                onChange={(number) => onChange({ ...value, discount_rate: number / 100 })}
              />
              <TextField
                label={t("appraisal:costSource")}
                value={value.cost_source}
                onChange={(event) => onChange({ ...value, cost_source: event.target.value })}
              />
              <p>{t("appraisal:costHint")}</p>
            </div>
          </Disclosure>
          <Disclosure title={t("appraisal:scenarios")} defaultOpen>
            <div className={styles.fields}>
              <p>{t("appraisal:scenarioHint")}</p>
              {value.scenarios.map((scenario, index) => (
                <fieldset key={scenario.name} className={styles.factors}>
                  <legend>{t(`appraisal:scenarioNames.${scenario.name}`)}</legend>
                  <AppraisalNumber
                    label={t("appraisal:demandFactor")}
                    value={scenario.demand_factor}
                    onChange={(demand_factor) =>
                      onChange({
                        ...value,
                        scenarios: value.scenarios.map((s, i) =>
                          i === index ? { ...s, demand_factor } : s,
                        ),
                      })
                    }
                  />
                  <AppraisalNumber
                    label={t("appraisal:valueFactor")}
                    value={scenario.value_factor}
                    onChange={(value_factor) =>
                      onChange({
                        ...value,
                        scenarios: value.scenarios.map((s, i) =>
                          i === index ? { ...s, value_factor } : s,
                        ),
                      })
                    }
                  />
                </fieldset>
              ))}
            </div>
          </Disclosure>
          {!projectReady(value) ? (
            <Banner tone="info" title={t("appraisal:incompleteForm")} />
          ) : null}
        </>
      ) : null}
    </div>
  )
}
