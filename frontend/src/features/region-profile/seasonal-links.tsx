import { useState } from "react"
import { LinkList, useRegionLinks } from "@/entities/link"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { Button, Card, EmptyState, ErrorState, Skeleton } from "@/shared/ui"

const PREVIEW = 8

export function SeasonalLinks({ regionId }: { readonly regionId: string }) {
  const { t } = useTranslation()
  const { season } = useSeason()
  const [expanded, setExpanded] = useState(false)
  const links = useRegionLinks(regionId, season)
  const rows = (links.data ?? []).filter((link) => link.season === season)
  if (links.isError)
    return <ErrorState title={t("profile:loadError")} onRetry={() => void links.refetch()} />
  if (!links.data) return <Skeleton lines={4} />
  const hidden = rows.length - PREVIEW
  return (
    <Card
      title={t("profile:onlySeason")}
      description={t("profile:onlyNote", { season: t(`data:season.${season}`) })}
    >
      {rows.length ? (
        <LinkList rows={expanded ? rows : rows.slice(0, PREVIEW)} />
      ) : (
        <EmptyState icon="link" title={t("profile:empty")} />
      )}
      {hidden > 0 ? (
        <Button
          variant="ghost"
          icon={expanded ? "minus" : "plus"}
          aria-expanded={expanded}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? t("profile:showLess") : t("profile:showAll", { count: rows.length })}
        </Button>
      ) : null}
    </Card>
  )
}
