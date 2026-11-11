import { useQuery } from "@tanstack/react-query"
import type { Map as LibreMap } from "maplibre-gl"
import { type RefObject, useEffect, useState } from "react"
import { api, unwrap } from "@/shared/api/client"
import { useStressView } from "@/shared/hooks/use-stress-view"

export function useVisibleStressPoints(engine: RefObject<LibreMap | null>, ready: boolean) {
  const view = useStressView()
  const [bounds, setBounds] = useState<readonly number[] | null>(null)
  useEffect(() => {
    const map = engine.current
    if (!map || !ready) return
    const move = () => {
      if (map.getZoom() < 6) return setBounds(null)
      const b = map.getBounds()
      setBounds([
        Math.max(-180, b.getWest()),
        Math.max(-90, b.getSouth()),
        Math.min(180, b.getEast()),
        Math.min(90, b.getNorth()),
      ])
    }
    move()
    map.on("moveend", move)
    return () => {
      map.off("moveend", move)
    }
  }, [engine, ready])
  return useQuery({
    queryKey: ["road-stress-map-points", view.jobId, bounds],
    enabled: view.showPoints !== false && view.jobId !== null && bounds !== null,
    queryFn: ({ signal }) =>
      unwrap(
        api.GET("/api/v1/road-stress-tests/{job_id}/impacts", {
          signal,
          params: {
            path: { job_id: view.jobId ?? "" },
            query: {
              west: bounds?.[0] ?? -180,
              south: bounds?.[1] ?? -90,
              east: bounds?.[2] ?? 180,
              north: bounds?.[3] ?? 90,
              limit: 200,
            },
          },
        }),
      ),
  })
}
