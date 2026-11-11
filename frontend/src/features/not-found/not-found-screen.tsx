import { useTranslation } from "@/shared/i18n"
import { ButtonLink, StatusScreen } from "@/shared/ui"
import { IsoText } from "@/shared/ui/brand"
import styles from "./not-found-screen.module.css"

export interface NotFoundScreenProps {
  readonly title: string
  readonly description: string
  readonly path?: string | undefined
}

export function NotFoundScreen({ title, description, path }: NotFoundScreenProps) {
  const { t } = useTranslation()
  return (
    <StatusScreen
      art={<IsoText glyph="notFound" />}
      title={title}
      description={description}
      actions={
        <>
          <ButtonLink to="/" icon="map">
            {t("common:action.home")}
          </ButtonLink>
          <ButtonLink to="/compare" variant="secondary" icon="compare">
            {t("common:notFound.compare")}
          </ButtonLink>
        </>
      }
    >
      {path === undefined ? null : (
        <p className={styles.path}>
          <span>{t("common:notFound.path")}</span>
          <code className={styles.code}>{path}</code>
        </p>
      )}
    </StatusScreen>
  )
}
