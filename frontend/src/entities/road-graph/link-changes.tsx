import type { LinkChange } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { linkChangeText } from "./link-change-text"
import { useLinkNames } from "./transport-links.queries"

export function LinkChanges({
  links,
  scenario,
  className,
}: {
  readonly links: readonly LinkChange[] | undefined
  readonly scenario: string
  readonly className?: string | undefined
}) {
  const { t } = useTranslation()
  const rows = links ?? []
  const names = useLinkNames(rows, scenario)
  if (!rows.length) return null
  return (
    <ul className={className} aria-label={t("graph:links.title")}>
      {rows.map((link) => {
        const text = linkChangeText(link, names)
        return (
          <li key={`${link.action}-${link.network}-${link.mode}-${link.source}-${link.target}`}>
            {t(text.key, text.values)}
          </li>
        )
      })}
    </ul>
  )
}
