import { useOverview, useRegions } from "@/entities/region"
import { PanelPending } from "../explorer-states"
import { MapPanel, type MapPanelProps } from "./map-panel"

export function ExplorerSummary(props: Omit<MapPanelProps, "overview" | "regions">) {
  const overview = useOverview()
  const regions = useRegions(props.season)
  if (overview.data && regions.data)
    return <MapPanel {...props} overview={overview.data} regions={regions.data} />
  return (
    <PanelPending
      failed={overview.isError || regions.isError}
      onRetry={() => {
        void overview.refetch()
        void regions.refetch()
      }}
    />
  )
}
