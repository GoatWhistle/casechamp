import { memo, useMemo, useState } from "react"
import type { AccessRow } from "@/entities/normative"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  DataTable,
  Disclosure,
  ErrorState,
  NoValue,
  Select,
  Skeleton,
  type TablePaginationState,
  type TableSort,
  TextField,
} from "@/shared/ui"
import styles from "./normative-result-table.module.css"

interface NormativeResultTableProps {
  readonly pagination?: TablePaginationState | undefined
  readonly search?: string | undefined
  readonly onSearch?: ((search: string) => void) | undefined
  readonly sort?: TableSort | undefined
  readonly onSortChange?: ((sort: TableSort) => void) | undefined
  readonly pending?: boolean
  readonly failed?: boolean
  readonly onRetry?: (() => void) | undefined
  readonly physicalOnly?: boolean
  readonly objectDestinations?: boolean
  readonly rows: AccessRow[]
  readonly walking: boolean
  readonly onPoint?: ((id: string, instant?: boolean) => void) | undefined
  readonly selectedPoint?: string | null | undefined
}

export const NormativeResultTable = memo(function NormativeResultTable({
  rows,
  walking,
  onPoint,
  selectedPoint,
  objectDestinations = false,
  physicalOnly = false,
  pagination,
  search: controlledSearch,
  onSearch,
  sort,
  onSortChange,
  pending = false,
  failed = false,
  onRetry,
}: NormativeResultTableProps) {
  const { t } = useTranslation()
  const [filter, setFilter] = useState("all")
  const [ownSearch, setOwnSearch] = useState("")
  const search = controlledSearch ?? ownSearch
  const setSearch = onSearch ?? setOwnSearch
  const needle = search.toLocaleLowerCase().trim()
  const filtered = useMemo(
    () =>
      pagination
        ? rows
        : rows.filter(
            (row) =>
              (filter === "all" || row.state === filter) &&
              `${row.name} ${row.id}`.toLocaleLowerCase().includes(needle),
          ),
    [rows, filter, needle, pagination],
  )
  const states = [
    "within",
    "exceeded",
    "unreachable",
    "unknown",
    "not_regulated",
    "not_applicable",
  ] as const
  return (
    <Disclosure title={t("normative:tableOpen")}>
      <TextField
        label={t("normative:pointSearch")}
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      {physicalOnly ? null : (
        <Select
          label={t("normative:filter")}
          value={filter}
          onChange={setFilter}
          options={[
            { value: "all", label: t("normative:all") },
            ...states.map((state) => ({ value: state, label: t(`normative:states.${state}`) })),
          ]}
        />
      )}
      <ResultTableRows
        rows={filtered}
        walking={walking}
        onPoint={onPoint}
        selectedPoint={selectedPoint}
        objectDestinations={objectDestinations}
        physicalOnly={physicalOnly}
        pagination={pagination}
        sort={sort}
        onSortChange={onSortChange}
        pending={pending}
        failed={failed}
        onRetry={onRetry}
      />
    </Disclosure>
  )
})

function ResultTableRows({
  rows,
  walking,
  onPoint,
  selectedPoint,
  objectDestinations,
  physicalOnly,
  pagination,
  sort,
  onSortChange,
  pending,
  failed,
  onRetry,
}: NormativeResultTableProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const costOf = (row: AccessRow) => (walking ? (row.distance_metres ?? null) : row.minutes)
  const costCell = (row: AccessRow) => {
    const value = costOf(row)
    return value === null ? <NoValue /> : f.number(value, 1)
  }
  if (pending) return <Skeleton lines={4} />
  if (failed) return <ErrorState title={t("normative:loadError")} onRetry={onRetry} />
  return (
    <DataTable<AccessRow>
      caption={t(
        walking
          ? "normative:residentialBuildings"
          : objectDestinations
            ? "normative:objectResults"
            : "normative:results",
      )}
      rows={rows}
      rowKey={(row) => row.id}
      selectedKey={selectedPoint}
      onRowClick={onPoint ? (row) => onPoint(row.id, true) : undefined}
      pageSize={pagination ? undefined : 50}
      pagination={pagination}
      manualSorting={Boolean(pagination)}
      sort={sort}
      onSortChange={onSortChange}
      className={styles.table}
      defaultSort={{ key: "cost", direction: "descending" }}
      columns={[
        {
          key: "name",
          header: t(
            walking
              ? "normative:building"
              : objectDestinations
                ? "normative:destinationObject"
                : "normative:point",
          ),
          cell: (row) => (
            <div className={styles.place}>
              <span className={styles.name}>{row.name}</span>
              <span className={styles.state}>
                {t(
                  physicalOnly
                    ? "normative:regionalQualificationUnknown"
                    : `normative:states.${row.state}`,
                )}
              </span>
            </div>
          ),
          sortValue: (row) => row.name,
        },
        {
          key: "cost",
          numeric: true,
          header: t(walking ? "normative:distanceMetres" : "normative:minutes"),
          cell: costCell,
          sortValue: costOf,
        },
      ]}
    />
  )
}
