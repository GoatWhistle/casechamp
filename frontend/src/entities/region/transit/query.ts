import { useMutation } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"
import type { components } from "@/shared/api/schema.gen"

export function useTransitJourney(regionId: string) {
  return useMutation({
    mutationFn: (
      body: Pick<
        components["schemas"]["TransitPlanRequest"],
        "origin_id" | "facility_id" | "departure_seconds"
      >,
    ) =>
      unwrap(
        api.POST("/api/v1/regions/{region_id}/transit-journeys", {
          params: { path: { region_id: regionId } },
          body: {
            horizon_seconds: 86400,
            maximum_walk_metres: 3000,
            transfer_seconds: 300,
            ...body,
          },
        }),
      ),
  })
}
