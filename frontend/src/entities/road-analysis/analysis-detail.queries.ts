import { useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"

export function useAnalysisDetail(analysisId: string, wayId: number | null) {
  return useQuery({
    queryKey: ["road-analysis-detail", analysisId, wayId],
    enabled: wayId !== null,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-analyses/{analysis_id}/results/{way_id}", {
          signal,
          params: { path: { analysis_id: analysisId, way_id: wayId ?? 0 } },
        }),
      ),
  })
}
