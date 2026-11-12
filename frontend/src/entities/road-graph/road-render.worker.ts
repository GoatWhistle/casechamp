import { api, isApiError, unwrap } from "@/shared/api/client"
import type { RoadRenderView, RoadWorkerRequest } from "@/shared/api/road-graph"
import { prepareRoadView } from "./road-render-data"

export type RoadWorkerResult =
  | { readonly data: RoadRenderView }
  | { readonly error: { readonly status: number; readonly code: string } }

self.addEventListener("message", async (event: MessageEvent<RoadWorkerRequest>) => {
  const { bounds, focus } = event.data
  const [west, south, east, north, zoom] = bounds
  try {
    const view = await unwrap(
      api.GET("/api/v1/road-graph", {
        params: {
          query: { west, south, east, north, zoom, ...(focus ? { region_id: focus.id } : {}) },
        },
      }),
    )
    self.postMessage({ data: prepareRoadView(view, focus) } satisfies RoadWorkerResult)
  } catch (error) {
    self.postMessage({
      error: isApiError(error)
        ? { status: error.status, code: error.code }
        : { status: 0, code: "network_unavailable" },
    } satisfies RoadWorkerResult)
  }
})
