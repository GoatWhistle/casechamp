import { useMutation, useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"
import type { components } from "@/shared/api/schema.gen"
import { trafficTerminal } from "@/shared/api/traffic"

export function useMunicipalTraffic(region: string, municipality: string) {
  return useQuery({
    queryKey: ["municipal-traffic", region, municipality],
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/municipal-scenarios/baseline/{region}/{municipality}", {
          params: { path: { region, municipality } },
          signal,
        }),
      ),
    staleTime: 300_000,
    retry: false,
  })
}

export function useMunicipalScenario() {
  return useMutation({
    mutationFn: (body: components["schemas"]["MunicipalScenarioRequest"]) =>
      unwrap(api.POST("/api/v1/municipal-scenarios", { body })),
  })
}

export function useMunicipalScenarioResult(identifier: string | null) {
  return useQuery({
    queryKey: ["municipal-scenario", identifier],
    enabled: identifier !== null,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/municipal-scenarios/{identifier}", {
          params: { path: { identifier: identifier ?? "" } },
          signal,
        }),
      ),
    refetchInterval: ({ state }) =>
      trafficTerminal(state.data?.status ?? "queued") ? false : 1000,
  })
}

export function useCancelMunicipalScenario() {
  return useMutation({
    mutationFn: (identifier: string) =>
      unwrap(
        api.POST("/api/v1/municipal-scenarios/{identifier}/cancel", {
          params: { path: { identifier } },
        }),
      ),
  })
}

export function useMunicipalEffects(identifier: string) {
  return useQuery({
    queryKey: ["municipal-effects", identifier],
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/municipal-scenarios/{identifier}/effects", {
          params: { path: { identifier } },
          signal,
        }),
      ),
    retry: false,
    staleTime: Infinity,
  })
}
