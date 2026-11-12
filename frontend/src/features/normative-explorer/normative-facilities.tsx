import { memo, useMemo, useState } from "react"
import type { Facility } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  ButtonLink,
  DataTable,
  Disclosure,
  ErrorState,
  Skeleton,
  type TablePaginationState,
  TextField,
} from "@/shared/ui"
import styles from "./normative-explorer.module.css"

export const NormativeFacilities = memo(function NormativeFacilities({
  facilities,
  pagination,
  search: controlledSearch,
  onSearch,
  pending = false,
  failed = false,
  onRetry,
}: {
  readonly pending?: boolean
  readonly failed?: boolean
  readonly onRetry?: (() => void) | undefined
  readonly pagination?: TablePaginationState | undefined
  readonly search?: string | undefined
  readonly onSearch?: ((search: string) => void) | undefined
  readonly facilities: readonly Facility[]
}) {
  const { t } = useTranslation()
  const [ownSearch, setOwnSearch] = useState("")
  const search = controlledSearch ?? ownSearch
  const setSearch = onSearch ?? setOwnSearch
  const filtered = useMemo(
    () =>
      pagination
        ? facilities
        : facilities.filter((row) =>
            `${row.name} ${row.address}`
              .toLocaleLowerCase()
              .includes(search.toLocaleLowerCase().trim()),
          ),
    [facilities, search, pagination],
  )
  return (
    <Disclosure title={t("normative:facilities")}>
      <div className={styles.facilities}>
        <TextField
          label={t("normative:facilitySearch")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        {pending ? (
          <Skeleton lines={4} />
        ) : failed ? (
          <ErrorState title={t("normative:loadError")} onRetry={onRetry} />
        ) : (
          <DataTable<Facility>
            caption={t("normative:facilities")}
            rows={filtered}
            rowKey={(row) => row.id}
            pageSize={pagination ? undefined : 10}
            pagination={pagination}
            sort={pagination ? null : undefined}
            defaultSort={{ key: "name", direction: "ascending" }}
            columns={[
              {
                key: "name",
                header: t("normative:mapFacility"),
                sortValue: pagination ? undefined : (row) => row.name,
                cell: (facility) => <FacilityDetails facility={facility} />,
              },
            ]}
          />
        )}
      </div>
    </Disclosure>
  )
})

function FacilityDetails({ facility }: { readonly facility: Facility }) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <Disclosure title={facility.name || t("normative:unnamedFacility")}>
      <div className={styles.facility}>
        <p>{facility.address}</p>
        <p>{t(`normative:coordinateStates.${facility.coordinate_status as "missing"}`)}</p>
        <p>{t("normative:observed", { date: f.date(facility.observed_at) })}</p>
        {facility.published_on ? (
          <p>
            {t("normative:facilityPublished", {
              date: f.date(facility.published_on),
            })}
          </p>
        ) : null}
        <ButtonLink to={facility.source_url} icon="external" variant="ghost">
          {t("normative:originSource")}
        </ButtonLink>
        {facility.source_sha256 ? (
          <Disclosure title={t("normative:documentVersion")}>
            <p className={styles.documentHash}>
              {t("normative:documentSha256", { hash: facility.source_sha256 })}
            </p>
          </Disclosure>
        ) : null}
        {facility.coordinate_snapshot_sha256 && facility.coordinate_snapshot_url ? (
          <Disclosure title={t("normative:coordinateVersion")}>
            <p className={styles.documentHash}>
              {t("normative:coordinateSnapshotSha256", {
                hash: facility.coordinate_snapshot_sha256,
              })}
            </p>
            <p>{t("normative:coordinateSnapshotNote")}</p>
            <ButtonLink to={facility.coordinate_snapshot_url} icon="external" variant="ghost">
              {t("normative:coordinateSnapshotSource")}
            </ButtonLink>
          </Disclosure>
        ) : null}
        {facility.coordinate_source ? (
          <ButtonLink to={facility.coordinate_source} icon="external" variant="ghost">
            {t("normative:coordinateSource")}
          </ButtonLink>
        ) : null}
      </div>
    </Disclosure>
  )
}
