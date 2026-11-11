import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { api, unwrap } from "@/shared/api/client"
import { useTranslation } from "@/shared/i18n"
import { Combobox } from "@/shared/ui"

export function StressPlace({
  label,
  onSelect,
}: {
  readonly label: string
  readonly onSelect: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const { t } = useTranslation()
  const places = useQuery({
    queryKey: ["graph-locations", query.trim(), null],
    enabled: query.trim().length >= 2,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-graph/locations", {
          signal,
          params: { query: { query: query.trim() } },
        }),
      ),
  })
  return (
    <Combobox
      label={label}
      minLength={2}
      placeholder={t("graph:connection.search")}
      loading={places.isFetching}
      groups={[
        {
          key: "places",
          label: t("graph:connection.places"),
          items: (places.data ?? [])
            .filter((p) => p.node !== null)
            .map((p) => ({ value: p.point_id, label: p.name, meta: p.region })),
        },
      ]}
      onQuery={(value) => {
        setQuery(value)
        onSelect("")
      }}
      onSelect={(item) => onSelect(item.value)}
      emptyText={t("graph:connection.noMatches")}
    />
  )
}
