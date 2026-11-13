import type { components } from "@/shared/api"
import { type MessageKey, useFormatters, useTranslation } from "@/shared/i18n"
import { HelpTip, NoValue } from "@/shared/ui"
import styles from "./municipal-social-effects.module.css"

type Effect = components["schemas"]["MunicipalSocialEffect"]

export function MunicipalSocialEffects({ rows }: { readonly rows: readonly Effect[] }) {
  const { t } = useTranslation()
  const f = useFormatters()
  if (!rows.length) return null
  return (
    <section className={styles.content} aria-label={t("map:municipalSocial.title")}>
      <div className={styles.heading}>
        <strong>{t("map:municipalSocial.title")}</strong>
        <HelpTip label={t("map:municipalSocial.title")} content={t("map:municipalSocial.help")} />
      </div>
      <table className={styles.table}>
        <thead>
          <tr>
            <th scope="col">{t("map:municipalSocial.service")}</th>
            <th scope="col">{t("map:municipalSocial.lost")}</th>
            <th scope="col">{t("map:municipalSocial.delayed")}</th>
            <th scope="col">{t("map:municipalSocial.exceeded")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.criterion_id}>
              <th scope="row">
                {t(`map:municipalSocial.services.${row.criterion_id}` as MessageKey, {
                  threshold: row.threshold_minutes,
                })}
                <HelpTip
                  label={t("map:municipalSocial.details")}
                  content={
                    row.status !== "available"
                      ? t("map:municipalCard.unavailable")
                      : t("map:municipalSocial.coverage", {
                          threshold: row.threshold_minutes,
                          total: row.reference_points ?? 0,
                          unresolved: row.unresolved_points ?? 0,
                        })
                  }
                />
              </th>
              {row.status === "available" ? (
                <>
                  <td data-alert={(row.lost_routes ?? 0) > 0}>
                    {f.number(row.lost_routes ?? 0, 0)}
                  </td>
                  <td data-alert={(row.delayed_points ?? 0) > 0}>
                    {f.number(row.delayed_points ?? 0, 0)}
                  </td>
                  <td data-alert={(row.crossed_threshold_points ?? 0) > 0}>
                    {f.number(row.crossed_threshold_points ?? 0, 0)}
                  </td>
                </>
              ) : (
                <td colSpan={3}>
                  <NoValue label={t("map:municipalCard.unavailable")} />
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
