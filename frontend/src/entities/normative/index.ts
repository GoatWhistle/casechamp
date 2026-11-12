import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { api, type components, unwrap } from "@/shared/api"

export type Criterion = components["schemas"]["CriterionResponse"]
export type Assessment = components["schemas"]["AssessmentResponse"]
export type AccessRow = components["schemas"]["AccessResponse"]
export type Facility = components["schemas"]["FacilityResponse"]

export function useNormativeCriteria(enabled = true) {
  return useQuery({
    queryKey: ["normative", "criteria"],
    enabled,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/normative/criteria", { signal })),
  })
}

export function useNormativeFacilities(id: string, enabled = true) {
  return useQuery({
    queryKey: ["normative", "facilities", id],
    enabled: enabled && id !== "",
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/criteria/{criterion_id}/facilities", {
          params: { path: { criterion_id: id } },
          signal,
        }),
      ),
  })
}

export function useLatestNormativeAssessment(id: string, enabled = true) {
  return useQuery({
    queryKey: ["normative", "latest", id],
    enabled: enabled && id !== "",
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/criteria/{criterion_id}/latest", {
          params: { path: { criterion_id: id } },
          signal,
        }),
      ),
    staleTime: 60_000,
  })
}

export function useNormativeAssessment() {
  const client = useQueryClient()
  return useMutation({
    onSuccess: (result) =>
      client.setQueryData(["normative", "latest", result.criterion.id], result),
    mutationFn: (body: components["schemas"]["AssessmentInput"]) =>
      unwrap(api.POST("/api/v1/normative/assessments", { body })),
  })
}

export { NormativeMap } from "./map/normative-map"

export function useNormativeRoute(
  runId: string,
  originId: string,
  stage: components["schemas"]["NormativeRouteResponse"]["stage"],
  regional = false,
) {
  return useQuery({
    queryKey: ["normative", "route", runId, originId, stage, regional],
    enabled: runId !== "" && originId !== "",
    staleTime: Number.POSITIVE_INFINITY,
    retry: false,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET(
          regional
            ? "/api/v1/normative/regional-measurements/{run_id}/routes/{origin_id}"
            : "/api/v1/normative/assessments/{run_id}/routes/{origin_id}",
          {
            params: { path: { run_id: runId, origin_id: originId }, query: { stage } },
            signal,
          },
        ),
      ) as Promise<components["schemas"]["NormativeRouteResponse"]>,
  })
}

export function useNormativeFireDestinations(enabled = true) {
  return useQuery({
    queryKey: ["normative", "fire-destinations"],
    enabled,
    queryFn: ({ signal }) => unwrap(api.GET("/api/v1/normative/fire-destinations", { signal })),
  })
}

export function useRegionalNormativeCatalog(regionId: string, criterionId: string, enabled = true) {
  return useQuery({
    queryKey: ["normative", "regional-catalog", regionId, criterionId],
    enabled: enabled && regionId !== "" && criterionId !== "",
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/regions/{region_id}/catalog/{criterion_id}", {
          params: { path: { region_id: regionId, criterion_id: criterionId } },
          signal,
        }),
      ),
  })
}

export { ArchiveNotice } from "./archive/archive-notice"
export {
  type IndexMapRegion,
  type RegionalIndex,
  useRegionalIndex,
  useRegionalIndexMap,
} from "./indices"
export {
  type RegionalMeasurement,
  useCalculateRegionalMeasurement,
  useRegionalMeasurement,
} from "./regional-measurements"
export {
  type RegionalMapView,
  type RegionalPointDetail,
  type RegionalRowOptions,
  type RegionalRunView,
  useRegionalFacilitiesPage,
  useRegionalMap,
  useRegionalPoint,
  useRegionalRows,
  useRegionalRunView,
} from "./regional-view"
