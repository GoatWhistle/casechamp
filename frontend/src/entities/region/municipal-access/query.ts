import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"
import type { components } from "@/shared/api/schema.gen"

type Target = components["schemas"]["MunicipalAccessMapTarget"]
async function load(target: Target, signal: AbortSignal) {
  const page = (offset: number) =>
    unwrap(
      api.GET("/api/v1/regions/{region_id}/municipalities/{municipality_id}/access", {
        params: {
          path: { region_id: target.region_id, municipality_id: target.municipality_id },
          query: {
            criterion_id: target.criterion_id,
            threshold: target.threshold,
            deficit_only: target.deficit_only ?? true,
            offset,
            limit: 1000,
          },
        },
        signal,
      }),
    )
  const first = await page(0)
  const points = [...first.points]
  while (points.length < first.total) {
    const next = await page(points.length)
    if (next.source_sha256 !== first.source_sha256 || !next.points.length)
      throw new Error("Municipal measurement changed during pagination")
    points.push(...next.points)
  }
  return { ...first, points }
}
export function useMunicipalAccess(target: Target | null) {
  return useQuery({
    queryKey: ["municipal-access", target],
    enabled: target !== null,
    staleTime: 30_000,
    queryFn: ({ signal }) => {
      if (!target) throw new Error("Municipal access target is required")
      return load(target, signal)
    },
  })
}
