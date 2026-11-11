import { useMutation, useQuery } from "@tanstack/react-query"
import { api, type components, isApiError, shouldRetry, unwrap } from "@/shared/api"

export type ScenarioCatalog = components["schemas"]["ScenarioCatalogResponse"]
export type MarketCity = components["schemas"]["MarketCityResponse"]
export type ScenarioRequest = components["schemas"]["ScenarioEvaluationRequest"]
export type ScenarioLink = components["schemas"]["TrunkLinkRequest"]
export type ScenarioResult = components["schemas"]["ScenarioEvaluationResponse"]
export type ScenarioRegionImpact = components["schemas"]["RegionImpactResponse"]
export type ScenarioSeason = ScenarioRequest["season"]
export type ScenarioMode = ScenarioLink["mode"]

const SCENARIO_DATA_MISSING = "data_unavailable"

export function isScenarioDataMissing(error: unknown): boolean {
  return isApiError(error) && error.code === SCENARIO_DATA_MISSING
}

export function useScenarioCatalog() {
  return useQuery({
    queryKey: ["scenario-catalog"],
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/scenarios", { signal })),
    staleTime: Number.POSITIVE_INFINITY,
    retry: (count, error) => !isScenarioDataMissing(error) && shouldRetry(count, error),
  })
}

export function useEvaluateScenario() {
  return useMutation({
    mutationFn: (body: ScenarioRequest) => unwrap(api.POST("/api/v1/scenarios/evaluate", { body })),
  })
}
