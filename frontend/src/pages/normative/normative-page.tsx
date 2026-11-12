import { NormativeExplorer } from "@/features/normative-explorer"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"
import { Banner, PageHeader } from "@/shared/ui"
import styles from "./normative-page.module.css"

export function NormativePage() {
  const { t } = useTranslation()
  useDocumentTitle(t("normative:title"))
  return (
    <div className={styles.page}>
      <PageHeader title={t("normative:title")} description={t("normative:lead")} />
      <NormativeExplorer />
      <Banner tone="neutral" title={t("normative:attribution")} />
    </div>
  )
}
