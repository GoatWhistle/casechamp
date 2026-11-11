import { clsx } from "clsx"
import { useTranslation } from "@/shared/i18n"
import { ButtonLink, Icon, Tooltip } from "@/shared/ui"
import type { Link } from "../link.queries"
import styles from "./link-list.module.css"

type SeasonKey = NonNullable<Link["season"]> | "unknown"

const SHORT_DISTANCE = 10

function rounded(value: number, digits: number): number {
  const scale = 10 ** digits
  return Math.round(value * scale) / scale
}

export interface LinkListProps {
  readonly rows: readonly Link[]
  readonly showMode?: boolean
  readonly className?: string | undefined
}

function LinkMeta({ link, showMode }: { readonly link: Link; readonly showMode: boolean }) {
  const { t } = useTranslation()
  const season: SeasonKey = link.season ?? "unknown"
  return (
    <div className={styles.metadata}>
      {showMode ? <span>{t(`data:mode.${link.mode}`)}</span> : null}
      <span>{t(`data:season.${season}`)}</span>
      {link.freq_per_week !== null && !link.freq_assumed ? (
        <span>{t("data:frequency.value", { value: rounded(link.freq_per_week, 1) })}</span>
      ) : null}
      {link.km === null ? null : (
        <span>
          {t("links:distance", { value: rounded(link.km, link.km < SHORT_DISTANCE ? 1 : 0) })}
        </span>
      )}
      {link.is_model ? <span className={styles.model}>{t("data:modelLink.badge")}</span> : null}
    </div>
  )
}

export function LinkList({ rows, showMode = true, className }: LinkListProps) {
  const { t } = useTranslation()
  return (
    <ul className={clsx(styles.list, className)}>
      {rows.map((link) => (
        <li key={link.id} data-link-id={link.id} className={styles.row}>
          <div className={styles.content}>
            <p className={styles.route}>
              <span>{link.from.name}</span>
              <Icon name="arrow-right" size="sm" className={styles.arrow} />
              <span>{link.to.name}</span>
            </p>
            <LinkMeta link={link} showMode={showMode} />
          </div>
          {link.source_url ? (
            <Tooltip
              content={t("links:source", { from: link.from.name, to: link.to.name })}
              describe={false}
            >
              <span className={styles.source}>
                <ButtonLink to={link.source_url} icon="external" variant="ghost">
                  <span className="visually-hidden">
                    {t("links:source", { from: link.from.name, to: link.to.name })}
                  </span>
                </ButtonLink>
              </span>
            </Tooltip>
          ) : null}
        </li>
      ))}
    </ul>
  )
}
