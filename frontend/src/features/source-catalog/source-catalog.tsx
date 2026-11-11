import { useSearchParams } from "react-router"
import { type Source, useSources } from "@/entities/reference"
import { useFormatters, useTranslation } from "@/shared/i18n"
import {
  ButtonLink,
  Card,
  Disclosure,
  EmptyState,
  ErrorState,
  NoValue,
  Skeleton,
  StatusBadge,
  Tabs,
  Tooltip,
} from "@/shared/ui"
import styles from "./source-catalog.module.css"
import { SourceNote } from "./source-note"
import { sourceTopic, sourceUsage, TOPIC_ICONS, TOPICS } from "./source-topics"

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

let rememberedTopic = "network"

function SourceEntry({ source }: { readonly source: Source }) {
  const { t } = useTranslation()
  const f = useFormatters()
  const usage = sourceUsage(source.id)
  const note = source.note ?? (source.id === "region-geometry" ? t("sources:geometry") : null)
  const period =
    source.period === null ? (
      <NoValue />
    ) : ISO_DATE.test(source.period) ? (
      f.date(source.period)
    ) : (
      source.period
    )
  return (
    <Card
      as="article"
      className={styles.entry}
      title={source.title}
      description={note === null ? undefined : <SourceNote text={note} />}
      actions={
        <div className={styles.actions}>
          <dl className={styles.metadata}>
            <div>
              <dt>{t("sources:period")}</dt>
              <dd>{period}</dd>
            </div>
            <div>
              <dt>{t("sources:rows")}</dt>
              <dd className={styles.count}>
                {source.rows === null ? <NoValue /> : f.integer(source.rows)}
              </dd>
            </div>
          </dl>
          <span className={styles.link}>
            {source.url ? (
              <Tooltip content={t("sources:openNamed", { title: source.title })} describe={false}>
                <span className={styles.linkAnchor}>
                  <ButtonLink
                    reloadDocument={source.url.startsWith("/datasets/")}
                    to={source.url}
                    variant="ghost"
                    icon="external"
                  >
                    <span className="visually-hidden">
                      {t("sources:openNamed", { title: source.title })}
                    </span>
                  </ButtonLink>
                </span>
              </Tooltip>
            ) : null}
          </span>
        </div>
      }
    >
      {source.url ? null : (
        <StatusBadge
          tone="neutral"
          icon="link"
          label={t("sources:inside")}
          className={styles.inside}
        />
      )}
      {usage === undefined ? null : (
        <div className={styles.usage}>
          <Disclosure title={t("sources:usage")}>
            <p>{t(`sources:uses.${usage}`)}</p>
          </Disclosure>
        </div>
      )}
    </Card>
  )
}

export function SourceCatalog() {
  const { t } = useTranslation()
  const sources = useSources()
  const [params, setParams] = useSearchParams()
  const present = TOPICS.filter(
    (key) => key !== "other" || sources.data?.some((source) => sourceTopic(source.id) === key),
  )
  const topic = present.find((key) => key === (params.get("topic") ?? rememberedTopic)) ?? "network"
  const entries = sources.data?.filter((source) => sourceTopic(source.id) === topic)
  return (
    <Tabs
      label={t("sources:topicsLabel")}
      items={present.map((value) => ({
        value,
        label: t(`sources:topics.${value}`),
        icon: TOPIC_ICONS[value],
      }))}
      value={topic}
      onChange={(next) => {
        rememberedTopic = next
        setParams(
          (current) => {
            const p = new URLSearchParams(current)
            p.set("topic", next)
            return p
          },
          { replace: true, preventScrollReset: true },
        )
      }}
    >
      {sources.isError ? (
        <ErrorState title={t("sources:loadError")} onRetry={() => void sources.refetch()} />
      ) : !sources.data ? (
        <Skeleton lines={8} />
      ) : (
        <div className={styles.catalog}>
          {entries?.map((source) => (
            <SourceEntry key={source.id} source={source} />
          ))}
          {entries?.length === 0 ? <EmptyState icon="database" title={t("sources:empty")} /> : null}
        </div>
      )}
    </Tabs>
  )
}
