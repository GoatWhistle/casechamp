import { useLocation } from "react-router"
import { NotFoundScreen } from "@/features/not-found"
import { useDocumentTitle, useTranslation } from "@/shared/i18n"

export function NotFoundPage() {
  const { t } = useTranslation()
  const { pathname } = useLocation()
  useDocumentTitle(t("common:notFound.title"))
  return (
    <NotFoundScreen
      title={t("common:notFound.title")}
      description={t("common:notFound.description")}
      path={pathname}
    />
  )
}
