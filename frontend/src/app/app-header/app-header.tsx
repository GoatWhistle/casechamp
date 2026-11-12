import type { ReactNode } from "react"
import { Link, NavLink, useMatch } from "react-router"
import { useMediaQuery } from "@/shared/hooks"
import { useSeason } from "@/shared/hooks/use-season"
import { useTranslation } from "@/shared/i18n"
import { Icon, type IconName, Tooltip } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import styles from "./app-header.module.css"

interface NavItem {
  readonly to: string
  readonly icon: IconName
  readonly label: "nav:map" | "nav:compare" | "nav:scenarios" | "nav:sources" | "nav:normative"
  readonly end?: boolean
}

const NAV: readonly NavItem[] = [
  { to: "/", icon: "map", label: "nav:map", end: true },
  { to: "/compare", icon: "compare", label: "nav:compare" },
  { to: "/scenarios", icon: "scenario", label: "nav:scenarios" },
  { to: "/sources", icon: "database", label: "nav:sources" },
]

const ICON_ONLY = "(width < 48rem)"

export interface AppHeaderProps {
  readonly search?: ReactNode
}

export function AppHeader({ search }: AppHeaderProps) {
  const { t } = useTranslation()
  const { seasonHref } = useSeason()
  const iconOnly = useMediaQuery(ICON_ONLY)
  const regionId = useMatch("/regions/:regionId")?.params.regionId
  const target = (item: NavItem) => (item.to === "/" && regionId ? `/?region=${regionId}` : item.to)
  return (
    <header className={styles.header}>
      <Link
        to={seasonHref("/")}
        viewTransition
        className={styles.brand}
        aria-label={t("common:app.name")}
      >
        <BrandMark size="fill" rings={2} decorative />
      </Link>
      <nav className={styles.nav} aria-label={t("nav:label")}>
        {NAV.map((item) => {
          const link = (
            <NavLink
              key={item.to}
              to={seasonHref(target(item))}
              end={item.end === true}
              viewTransition
              aria-label={t(item.label)}
              className={({ isActive }) =>
                isActive ? `${styles.link} ${styles.active}` : styles.link
              }
            >
              <Icon name={item.icon} size="lg" />
              <span className={styles.label} aria-hidden="true">
                {t(item.label)}
              </span>
            </NavLink>
          )
          return iconOnly ? (
            <Tooltip key={item.to} content={t(item.label)} side="bottom" describe={false}>
              {link}
            </Tooltip>
          ) : (
            link
          )
        })}
      </nav>
      {search ? <div className={styles.search}>{search}</div> : null}
    </header>
  )
}
