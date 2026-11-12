import { useCallback } from "react"
import {
  boundaryName,
  modelRegionId,
  type RegionSummary as Region,
  type Season,
} from "@/entities/region"
import { useTranslation } from "@/shared/i18n"
import { Skeleton } from "@/shared/ui"
import { OutsideRegion, RegionSummary } from "./region-summary"

export function useRegionCard(
  regions: readonly Region[] | undefined,
  season: Season,
  boundaries: Parameters<typeof boundaryName>[1],
  onClose: () => void,
) {
  return useCallback(
    (id: string) => {
      if (!regions) return <Skeleton lines={4} />
      const model = modelRegionId(id, regions)
      if (model)
        return <RegionSummary id={model} season={season} regions={regions} onClose={onClose} />
      return (
        <OutsideRegion
          name={boundaryName(id, boundaries) ?? id}
          count={regions.length}
          onClose={onClose}
        />
      )
    },
    [regions, season, boundaries, onClose],
  )
}

export function RegionSelectionStatus({ name }: { readonly name: string | undefined }) {
  const { t } = useTranslation()
  return (
    <p className="visually-hidden" role="status">
      {name ? t("map:selectedStatus", { name }) : ""}
    </p>
  )
}
