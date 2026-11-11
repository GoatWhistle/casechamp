import type { StressImpact } from "@/shared/api/road-stress"
import { useTranslation } from "@/shared/i18n"
import { Disclosure } from "@/shared/ui"

export function StressPointDetail({ impact }: { readonly impact: StressImpact }) {
  const { t } = useTranslation()
  return (
    <Disclosure title={impact.point.name} defaultOpen>
      <p>{impact.point.region}</p>
      <p>{t("stress:pointPopulation", { count: impact.point.population })}</p>
      <p>
        {t(impact.external_isolation ? "stress:isolated" : "stress:delay", {
          minutes: Math.round(impact.delay_minutes),
          markets: impact.lost_markets,
        })}
      </p>
      <p>{t("stress:directions")}</p>
      {(impact.markets ?? []).slice(0, 10).map((market) => (
        <p key={market.market}>
          <strong>{market.market}</strong>{" "}
          {market.after_hours === null
            ? t("stress:noPath")
            : t("stress:directionTimes", {
                before: Math.round(market.before_hours * 60),
                after: Math.round(market.after_hours * 60),
              })}
        </p>
      ))}
    </Disclosure>
  )
}
