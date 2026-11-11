import { type MessageKey, useTranslation } from "@/shared/i18n"

const messages: Readonly<Record<string, MessageKey>> = {
  lanes_without_verified_flow_no_time_effect: "graph:profile.unknownFlow",
  missing_lanes_default_one_per_direction: "graph:profile.defaultLanes",
  manual_new_connection_time: "graph:profile.manualConnection",
}

export function RoadCostNotes({ notes }: { readonly notes: readonly string[] | null | undefined }) {
  const { t } = useTranslation()
  return (
    <>
      {(notes ?? []).map((note) => (messages[note] ? <p key={note}>{t(messages[note])}</p> : null))}
    </>
  )
}
