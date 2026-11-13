import { useCallback, useState } from "react"
import type { ChatMapCommand, MapCommandHandler } from "@/shared/api/chat-map"
import { clearMunicipalAccess, showMunicipalAccess } from "@/shared/hooks/use-municipal-access-view"
import { showTransitJourney } from "@/shared/hooks/use-transit-view"

export function useMapSelection(
  regions: readonly { readonly id: string }[] | undefined,
  select: (id: string | null) => void,
) {
  const [mapCommand, setMapCommand] = useState<ChatMapCommand | null>(null)
  const selectRegion = useCallback(
    (id: string | null) => {
      clearMunicipalAccess()
      showTransitJourney(null)
      setMapCommand(null)
      select(id)
    },
    [select],
  )
  const onMapCommand = useCallback<MapCommandHandler>(
    (command) => {
      if (command.action === "focus") {
        if (!command.region_ids.every((id) => regions?.some((region) => region.id === id))) return
        select(command.region_ids.length === 1 ? (command.region_ids[0] ?? null) : null)
      }
      if (command.action === "focus_settlement" && command.settlement)
        select(command.settlement.region_id)
      if (command.action === "reset") select(null)
      applyMunicipalTarget(command)
      setMapCommand({ ...command })
    },
    [regions, select],
  )
  return { mapCommand, setMapCommand, selectRegion, onMapCommand }
}

function applyMunicipalTarget(command: ChatMapCommand) {
  if (command.action !== "zoom_in" && command.action !== "zoom_out")
    showTransitJourney(command.transit ?? null)
  if (command.municipal_access) showMunicipalAccess(command.municipal_access)
  else clearMunicipalAccess()
}
