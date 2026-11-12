import type { RegionalIndex } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { ButtonLink } from "@/shared/ui"

export function IndexReview({ index }: { readonly index: RegionalIndex }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const review = index.basis?.review
  if (!review) return <p>{t("normative:indexCurrentness")}</p>
  return (
    <>
      <p>
        {t(
          review.scope === "registry_listing"
            ? "normative:indexReviewRegistry"
            : "normative:indexReviewConsolidated",
          { date: f.date(review.as_of) },
        )}
      </p>
      <p>{t("normative:indexReviewLocation", { locator: review.locator })}</p>
      <p>{t("normative:indexReviewCaution")}</p>
      <ButtonLink to={review.source_url} icon="external" variant="ghost">
        {t("normative:indexReviewSource")}
      </ButtonLink>
    </>
  )
}

export function PopulationReference({
  value,
}: {
  readonly value: RegionalIndex["scenario"][number]
}) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (value.population === null || value.within_population === null) return null
  return (
    <p>
      {t("normative:indexPopulationCount", {
        within: f.integer(value.within_population),
        total: f.integer(value.population),
      })}
    </p>
  )
}
