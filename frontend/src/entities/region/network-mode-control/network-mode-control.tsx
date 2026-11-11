import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useTranslation } from "@/shared/i18n"
import { Select, type SelectVariant } from "@/shared/ui"
import { useOverview } from "../region.queries"

interface NetworkModeControlProps {
  readonly hideLabel?: boolean
  readonly variant?: SelectVariant
}

export function NetworkModeControl({ hideLabel = false, variant }: NetworkModeControlProps) {
  const { t } = useTranslation()
  const overview = useOverview()
  const snapshot = overview.data?.index.components.some((c) => c.key === "snapshot_network")
  const { networkMode, setNetworkMode } = useNetworkMode()
  return (
    <Select
      label={t("data:network.label")}
      hideLabel={hideLabel}
      {...(variant === undefined ? {} : { variant })}
      value={networkMode}
      onChange={setNetworkMode}
      options={[
        { value: "road", label: t(snapshot ? "graph:base" : "data:network.road") },
        {
          value: "multimodal",
          label: t(snapshot ? "graph:seasonalNetwork" : "data:network.multimodal"),
        },
      ]}
    />
  )
}
