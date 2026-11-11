import type { ReactNode } from "react"
import { useSearchParams } from "react-router"
import { useRegion } from "@/entities/region"
import { useNetworkMode } from "@/shared/hooks/use-network-mode"
import { useSeason } from "@/shared/hooks/use-season"
import { type MessageKey, useErrorText, useTranslation } from "@/shared/i18n"
import { ButtonLink, ErrorState, type IconName, PageHeader, Skeleton, Tabs } from "@/shared/ui"
import { LinksWorkspace } from "./links-workspace"
import styles from "./region-profile.module.css"

export interface RegionProfileProps {
  readonly regionId: string
  readonly calendar: ReactNode
  readonly settlements: ReactNode
  readonly actions?: ReactNode
}

type Section = "links" | "settlements" | "winter-calendar"

const UGRA = "71800000"

function resolveSection(params: URLSearchParams, isUgra: boolean): Section {
  const requested = params.get("section")
  if (isUgra && requested === "winter-calendar") return "winter-calendar"
  if (requested === "settlements") return "settlements"
  if (requested === null && params.has("settlement")) return "settlements"
  return "links"
}

function sectionItems(
  isUgra: boolean,
): readonly { value: Section; label: MessageKey; icon: IconName }[] {
  return [
    { value: "links", label: "profile:links", icon: "link" },
    { value: "settlements", label: "region:settlements.title", icon: "home" },
    ...(isUgra
      ? ([{ value: "winter-calendar", label: "profile:winter", icon: "calendar" }] as const)
      : []),
  ]
}

export function RegionProfile({ regionId, calendar, settlements, actions }: RegionProfileProps) {
  const { t } = useTranslation()
  const errorText = useErrorText()
  const { season, seasonHref } = useSeason()
  const { networkMode } = useNetworkMode()
  const [params, setParams] = useSearchParams()
  const region = useRegion(regionId, season)
  const data = region.data
  const isUgra = regionId === UGRA
  const section = resolveSection(params, isUgra)
  if (region.isError)
    return (
      <ErrorState
        title={t("region:loadError")}
        description={errorText(region.error)}
        onRetry={() => void region.refetch()}
        retryPending={region.isFetching}
      />
    )
  if (!data || data.id !== regionId) return <Skeleton lines={12} />
  const content: Record<Section, ReactNode> = {
    links: <LinksWorkspace regionId={regionId} data={data} isUgra={isUgra} />,
    settlements,
    "winter-calendar": calendar,
  }
  return (
    <div className={styles.profile}>
      <ButtonLink
        to={seasonHref("/")}
        variant="ghost"
        size="compact"
        icon="arrow-left"
        className={styles.back}
      >
        {t("region:backToMap")}
      </ButtonLink>
      <PageHeader
        title={data.name}
        actions={
          <>
            {actions}
            <ButtonLink
              to={`/compare?ids=${data.id}&season=${season}&network_mode=${networkMode}`}
              variant="secondary"
              icon="compare"
            >
              {t("region:compare")}
            </ButtonLink>
          </>
        }
      />
      <Tabs
        label={t("profile:sections")}
        items={sectionItems(isUgra).map((item) => ({
          ...item,
          label: t(item.label),
        }))}
        value={section}
        onChange={(next) =>
          setParams(
            (current) => {
              const p = new URLSearchParams(current)
              p.set("section", next)
              return p
            },
            { preventScrollReset: true },
          )
        }
      >
        {content[section]}
      </Tabs>
    </div>
  )
}
