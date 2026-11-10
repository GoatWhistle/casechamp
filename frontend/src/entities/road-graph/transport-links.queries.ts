import { useQuery } from "@tanstack/react-query"
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

export function useLinkNames(links: readonly LinkChange[]): LinkNames {
  const ids = [
    ...new Set(
      links
        .filter((link) => link.network === "local")
        .flatMap((link) => [link.source, link.target])
        .filter((id) => id !== "*"),
    ),
  ].sort()
  const query = useQuery({
    queryKey: ["road-graph-places", ids],
    enabled: ids.length > 0,
    staleTime: Number.POSITIVE_INFINITY,
    queryFn: ({ signal }) =>
      unwrap(api.GET("/api/v1/road-graph/places", { signal, params: { query: { ids } } })),
  })
  return new Map((query.data ?? []).map((place) => [place.point_id, place.name]))
}
