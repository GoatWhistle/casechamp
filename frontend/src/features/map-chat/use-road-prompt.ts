import { useEffect, useRef } from "react"
import type { RoadSegment } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"

export function useRoadPrompt(
  roads: readonly RoadSegment[],
  draft: string,
  setDraft: (draft: string) => void,
) {
  const { t } = useTranslation()
  const auto = useRef("")
  const latest = useRef({ draft, setDraft })
  latest.current = { draft, setDraft }
  useEffect(() => {
    const name = roads.length === 1 ? roads[0]?.name : ""
    const next = !roads.length
      ? ""
      : name
        ? t("chat:roads.closeNamed", { name })
        : roads.length === 1
          ? t("chat:roads.closeOne")
          : t("chat:roads.close", { count: roads.length })
    const current = latest.current.draft
    if ((current.trim() === "" || current === auto.current) && current !== next)
      latest.current.setDraft(next)
    auto.current = next
  }, [roads, t])
}
