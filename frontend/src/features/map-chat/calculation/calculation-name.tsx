import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"
import { useTranslation } from "@/shared/i18n"

export function CalculationName({ id, index }: { readonly id: string; readonly index: number }) {
  const { t } = useTranslation()
  const geometry = useQuery({
    queryKey: ["road-stress-geometry", id],
    staleTime: Infinity,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}/geometry", {
          signal,
          params: { path: { job_id: id } },
        }),
      ),
  })
  const names =
    geometry.data?.names.filter((name) => /^[\p{L}]+[-‑– ]\d+[\p{L}\d-]*$/u.test(name)) ?? []
  return (
    <strong>
      {names.length
        ? t("chat:calculationRun.closure", {
            roads: names
              .toSorted((a, b) => a.localeCompare(b, "ru", { numeric: true }))
              .join(" + "),
          })
        : t("chat:calculationRun.job", { index })}
    </strong>
  )
}
