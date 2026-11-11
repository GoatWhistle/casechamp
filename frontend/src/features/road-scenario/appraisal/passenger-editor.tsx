import { useState } from "react"
import { useGraphLocations } from "@/entities/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, Combobox, Select } from "@/shared/ui"
import { AppraisalNumber } from "./appraisal-number"
import { AppraisalSource } from "./appraisal-source"
import type { Passenger } from "./appraisal-state"

export function PassengerEditor({
  value,
  markets,
  regionId,
  onChange,
  onRemove,
}: {
  readonly value: Passenger
  readonly markets: readonly string[]
  readonly regionId: string | null
  readonly onChange: (value: Passenger) => void
  readonly onRemove: () => void
}) {
  const { t } = useTranslation()
  const [query, setQuery] = useState("")
  const search = useGraphLocations(query, regionId)
  return (
    <>
      <Combobox
        label={t("appraisal:origin")}
        minLength={2}
        placeholder={value.origin_name || value.origin_point_id || t("graph:connection.search")}
        groups={[
          {
            key: "places",
            label: t("graph:connection.places"),
            items: (search.data ?? []).map((p) => ({
              value: p.point_id,
              label: p.name,
              meta: p.region,
            })),
          },
        ]}
        onQuery={(next) => {
          setQuery(next)
          if (next.trim()) onChange({ ...value, origin_point_id: "", origin_name: "" })
        }}
        onSelect={(item) =>
          onChange({ ...value, origin_point_id: item.value, origin_name: item.label })
        }
        loading={search.isFetching}
        emptyText={t("graph:connection.noMatches")}
      />
      {search.isError ? <Banner tone="danger" title={t("graph:connection.searchError")} /> : null}
      <Select
        label={t("appraisal:market")}
        value={value.market_city || null}
        options={markets.map((name) => ({ value: name, label: name }))}
        onChange={(market_city) => onChange({ ...value, market_city })}
      />
      <AppraisalNumber
        label={t("appraisal:passengerTrips")}
        value={value.trips_per_year}
        onChange={(trips_per_year) => onChange({ ...value, trips_per_year })}
      />
      <AppraisalNumber
        label={t("appraisal:valueOfTime")}
        value={value.rub_per_hour}
        onChange={(rub_per_hour) => onChange({ ...value, rub_per_hour })}
      />
      <AppraisalSource
        source={value.source}
        basis={value.basis ?? "assumed"}
        onSource={(source) => onChange({ ...value, source })}
        onBasis={(basis) => onChange({ ...value, basis })}
      />
      <Button icon="trash" variant="ghost" onClick={onRemove}>
        {t("appraisal:removeFlow")}
      </Button>
    </>
  )
}
