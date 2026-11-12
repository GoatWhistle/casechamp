import { type Season, useMunicipalityIndices } from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { ErrorState, Skeleton } from "@/shared/ui"
import { MunicipalityCardFrame } from "./municipality-card-frame"
import { MunicipalityConnectivity } from "./municipality-connectivity"
import styles from "./municipality-index-card.module.css"
import { MunicipalityOtherServices } from "./municipality-other-services"
import { MunicipalityServices } from "./municipality-services"

export function MunicipalityIndexCard({
  regionId,
  municipalityId,
  name,
  season,
  onClear,
}: {
  readonly regionId: string
  readonly municipalityId: string
  readonly name: string
  readonly season: Season
  readonly onClear: () => void
}) {
  const query = useMunicipalityIndices(regionId, municipalityId, season)
  const { t } = useTranslation()
  const data = query.data
  return (
    <MunicipalityCardFrame name={name} onClear={onClear}>
      {query.isPending ? (
        <Skeleton lines={5} />
      ) : query.isError ? (
        <ErrorState title={t("map:municipalCard.loadError")} onRetry={() => void query.refetch()} />
      ) : data ? (
        <div className={styles.content}>
          <MunicipalityServices rows={data.normative} />
          <MunicipalityOtherServices rows={data.normative} />
          <MunicipalityConnectivity data={data} />
        </div>
      ) : null}
    </MunicipalityCardFrame>
  )
}
