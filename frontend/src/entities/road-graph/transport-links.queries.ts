import { useQueries, useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api/client"
import type { LinkChange, LinkNetwork, ScenarioNetwork } from "@/shared/api/road-graph"
import type { LinkNames } from "./link-change-text"

export interface TransportLinkSearch {
  readonly network: LinkNetwork
  readonly place: string
  readonly scenario: ScenarioNetwork
}

function fetchLinks(search: TransportLinkSearch, signal: AbortSignal, mode?: string) {
  return unwrap(
    api.GET("/api/v1/transport-links", {
      signal,
      params: {
        query: {
          network: search.network,
          place: search.place,
          scenario: search.scenario,
          ...(mode ? { mode } : {}),
        },
      },
    }),
  )
}

export function useTransportLinks(search: TransportLinkSearch | null) {
  return useQuery({
    queryKey: ["transport-links", search],
    enabled: search !== null && search.place.trim().length > 0,
    queryFn: ({ signal }) =>
      fetchLinks(search ?? { network: "intercity", place: "", scenario: "road" }, signal),
  })
}

export function useLinkNames(links: readonly LinkChange[], scenario: string): LinkNames {
  const season: ScenarioNetwork = scenario === "summer" || scenario === "winter" ? scenario : "road"
  const sources = [
    ...new Set(links.filter((link) => link.network === "local").map((link) => link.source)),
  ]
  const results = useQueries({
    queries: sources.map((place) => ({
      queryKey: ["transport-links", { network: "local", place, scenario: season }],
      staleTime: Number.POSITIVE_INFINITY,
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        fetchLinks({ network: "local", place, scenario: season }, signal),
    })),
  })
  const names = new Map<string, string>()
  for (const result of results)
    for (const row of result.data ?? []) {
      names.set(row.source, row.source_name)
      names.set(row.target, row.target_name)
    }
  return names
}
