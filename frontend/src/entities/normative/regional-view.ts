import { useQuery } from "@tanstack/react-query"
import { api, type components, type paths, unwrap } from "@/shared/api"
import type { NormativeRouteStage, RegionalViewport } from "@/shared/api/normative-map"

export type RegionalRunView = components["schemas"]["RegionalRunViewResponse"]
export type RegionalMapView = components["schemas"]["RegionalMapViewResponse"]
export type RegionalPointDetail = components["schemas"]["RegionalPointDetailResponse"]
export type RegionalRowOptions = NonNullable<
  paths["/api/v1/normative/regional-measurements/{run_id}/rows"]["get"]["parameters"]["query"]
>

export function useRegionalRunView(regionId: string, criterionId: string, enabled = true) {
  return useQuery({
    queryKey: ["normative", "regional-view", regionId, criterionId],
    enabled: enabled && regionId !== "" && criterionId !== "",
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/regions/{region_id}/measurements/{criterion_id}/view", {
          params: { path: { region_id: regionId, criterion_id: criterionId } },
          signal,
        }),
      ),
  })
}

export function useRegionalRows(runId: string, options: RegionalRowOptions) {
  return useQuery({
    queryKey: ["normative", "regional-rows", runId, options],
    enabled: runId !== "",
    staleTime: Infinity,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/regional-measurements/{run_id}/rows", {
          params: { path: { run_id: runId }, query: options },
          signal,
        }),
      ),
  })
}

export function useRegionalFacilitiesPage(runId: string, page: number, search: string) {
  return useQuery({
    queryKey: ["normative", "regional-facilities", runId, page, search],
    enabled: runId !== "",
    staleTime: Infinity,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/regional-measurements/{run_id}/facilities", {
          params: { path: { run_id: runId }, query: { page: page + 1, page_size: 10, search } },
          signal,
        }),
      ),
  })
}

export function useRegionalPoint(
  runId: string,
  originId: string | null,
  stage: NormativeRouteStage,
) {
  return useQuery({
    queryKey: ["normative", "regional-point", runId, originId, stage],
    enabled: runId !== "" && Boolean(originId),
    staleTime: Infinity,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/normative/regional-measurements/{run_id}/points/{origin_id}", {
          params: { path: { run_id: runId, origin_id: originId ?? "" }, query: { stage } },
          signal,
        }),
      ),
  })
}

export function useRegionalMap(
  runId: string,
  stage: NormativeRouteStage,
  viewport: RegionalViewport | null,
  enabled: boolean,
) {
  return useQuery<RegionalMapView>({
    queryKey: ["normative", "regional-map", runId, stage, viewport],
    placeholderData: (previous: RegionalMapView | undefined) =>
      previous?.run_id === runId && previous.stage === stage ? previous : undefined,
    enabled: enabled && runId !== "" && viewport !== null,
    staleTime: Infinity,
    queryFn: ({ signal }) => fetchRegionalMap(runId, stage, viewport, signal),
  })
}

async function fetchRegionalMap(
  runId: string,
  stage: NormativeRouteStage,
  viewport: RegionalViewport | null,
  signal: AbortSignal,
) {
  const result = await unwrap(
    api.GET("/api/v1/normative/regional-measurements/{run_id}/map", {
      params: {
        path: { run_id: runId },
        query: {
          stage,
          west: viewport?.west ?? -180,
          east: viewport?.east ?? 180,
          south: viewport?.south ?? -90,
          north: viewport?.north ?? 90,
          zoom: viewport?.zoom ?? 5,
        },
      },
      signal,
    }),
  )
  return {
    ...result,
    cells: result.cells.map((cell) => ({ ...cell, bounds: mapBounds(cell.bounds) })),
    facilities: result.facilities.map((cell) => ({ ...cell, bounds: mapBounds(cell.bounds) })),
  }
}

function mapBounds(values: number[]): [number, number, number, number] {
  const [west, south, east, north] = values
  if (
    values.length !== 4 ||
    west === undefined ||
    south === undefined ||
    east === undefined ||
    north === undefined
  ) {
    throw new Error("Invalid regional map bounds")
  }
  return [west, south, east, north]
}
