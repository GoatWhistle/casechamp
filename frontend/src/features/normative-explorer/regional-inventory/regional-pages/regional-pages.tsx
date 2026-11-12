import { useState } from "react"
import {
  type RegionalRunView,
  useRegionalFacilitiesPage,
  useRegionalRows,
} from "@/entities/normative"
import type { NormativeRouteStage } from "@/shared/api/normative-map"
import type { TableSort } from "@/shared/ui"
import { NormativeFacilities } from "../../normative-facilities"
import { NormativeResultTable } from "../../normative-result-table"

export function RegionalRows({
  view,
  stage,
  selectedPoint,
  onPoint,
}: {
  readonly view: RegionalRunView
  readonly stage: NormativeRouteStage
  readonly selectedPoint: string | null
  readonly onPoint: (id: string, instant?: boolean) => void
}) {
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState("")
  const [sort, setSort] = useState<TableSort>({ key: "cost", direction: "descending" })
  const key = sort.key === "name" ? "name" : "cost"
  const query = useRegionalRows(view.run_id, {
    stage,
    page: page + 1,
    page_size: 50,
    sort: key,
    descending: sort.direction === "descending",
    search,
  })
  return (
    <NormativeResultTable
      physicalOnly
      rows={query.data?.rows ?? []}
      walking={view.unit === "metres"}
      selectedPoint={selectedPoint}
      onPoint={onPoint}
      pagination={{
        page,
        pageSize: 50,
        totalRows: query.data?.total ?? view.origins,
        onPage: setPage,
      }}
      search={search}
      onSearch={(value) => {
        setSearch(value)
        setPage(0)
      }}
      sort={sort}
      onSortChange={(value) => {
        setSort(value)
        setPage(0)
      }}
      pending={query.isPending}
      failed={query.isError}
      onRetry={() => void query.refetch()}
    />
  )
}

export function RegionalFacilities({
  runId,
  total,
}: {
  readonly runId: string
  readonly total: number
}) {
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState("")
  const query = useRegionalFacilitiesPage(runId, page, search)
  return (
    <NormativeFacilities
      facilities={query.data?.facilities ?? []}
      pagination={{ page, pageSize: 10, totalRows: query.data?.total ?? total, onPage: setPage }}
      search={search}
      onSearch={(value) => {
        setSearch(value)
        setPage(0)
      }}
      pending={query.isPending}
      failed={query.isError}
      onRetry={() => void query.refetch()}
    />
  )
}
