import { useMunicipalEffects } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Button, Skeleton } from "@/shared/ui"

import { MunicipalSocialEffects } from "./social/municipal-social-effects"

export function MunicipalLocalEffects({ identifier }: { readonly identifier: string }) {
  const query = useMunicipalEffects(identifier)
  const { t } = useTranslation()
  if (query.isPending) return <Skeleton lines={3} />
  if (query.isError)
    return (
      <Button variant="ghost" onClick={() => void query.refetch()}>
        {t("map:municipalTraffic.retryEffects")}
      </Button>
    )
  const { before, after } = query.data
  return (
    <div>
      <p>
        <strong>{t("map:municipalTraffic.localEffects")}</strong>
      </p>
      <p>
        {t("map:municipalTraffic.time", {
          before: before.vehicle_hours_on_local_edges,
          after: after.vehicle_hours_on_local_edges,
        })}
      </p>
      <p>
        {t("map:municipalTraffic.lost", {
          before: before.unserved_departures,
          after: after.unserved_departures,
        })}
      </p>
      <p>
        {t("map:municipalTraffic.overload", {
          before: before.overloaded_directed_edges,
          after: after.overloaded_directed_edges,
        })}
      </p>
      <MunicipalSocialEffects rows={query.data.social ?? []} />
    </div>
  )
}
