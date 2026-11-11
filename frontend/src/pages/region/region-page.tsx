import { useParams, useSearchParams } from "react-router"
import { useRegion } from "@/entities/region"
import { NotFoundScreen } from "@/features/not-found"
import { RegionProfile } from "@/features/region-profile"
import { RegionSettlements } from "@/features/region-settlements"
import { RegionSummary } from "@/features/region-summary"
import { WinterCalendar } from "@/features/winter-calendar"
import { isApiError } from "@/shared/api"
import { useSeason } from "@/shared/hooks/use-season"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { ButtonLink, Card } from "@/shared/ui"
import styles from "./region-page.module.css"

export function RegionPage() {
  const { regionId = "" } = useParams()
  const { season } = useSeason()
  const [params, setParams] = useSearchParams()
  const highlight = params.get("settlement")
  const region = useRegion(regionId, season)
  const missing = isApiError(region.error) && region.error.status === 404
  const { t } = useTranslation()
  useDocumentTitle(
    missing ? t("region:missing.title") : (region.data?.name ?? t("region:fallbackTitle")),
  )
  if (missing)
    return (
      <NotFoundScreen
        title={t("region:missing.title")}
        description={t("region:missing.description")}
      />
    )
  return (
    <div className={styles.page}>
      <RegionProfile
        regionId={regionId}
        calendar={<WinterCalendar />}
        actions={
          <ButtonLink
            to={`/?region=${regionId}&season=${season}&panel=scenario`}
            variant="secondary"
            icon="route"
          >
            {t("profile:openScenario")}
          </ButtonLink>
        }
        settlements={
          <div className={styles.settlements}>
            <Card as="section" title={t("region:summary")}>
              <RegionSummary region={region.data} />
            </Card>
            <RegionSettlements
              regionId={regionId}
              highlightId={highlight}
              onHighlight={(id) =>
                setParams(
                  (current) => {
                    const p = new URLSearchParams(current)
                    p.set("settlement", id)
                    return p
                  },
                  { replace: true, preventScrollReset: true },
                )
              }
            />
          </div>
        }
      />
    </div>
  )
}
