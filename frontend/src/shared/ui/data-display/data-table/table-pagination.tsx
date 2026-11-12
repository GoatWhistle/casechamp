import { useFormatters, useTranslation } from "../../../i18n"
import { Button } from "../../primitives/button/button"
import styles from "./table-pagination.module.css"

interface TablePaginationProps {
  readonly caption: string
  readonly page: number
  readonly pages: number
  readonly onPage: (page: number) => void
}

export function TablePagination({ caption, page, pages, onPage }: TablePaginationProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  return (
    <nav
      className={styles.pagination}
      aria-label={t("common:ui.pagination.label", { table: caption })}
    >
      <Button
        variant="ghost"
        size="compact"
        icon="arrow-left"
        disabled={page === 0}
        onClick={() => onPage(page - 1)}
      >
        {t("common:ui.pagination.previous")}
      </Button>
      <span aria-live="polite">
        {t("common:ui.pagination.page", { page: f.integer(page + 1), pages: f.integer(pages) })}
      </span>
      <Button
        variant="ghost"
        size="compact"
        icon="arrow-right"
        disabled={page + 1 >= pages}
        onClick={() => onPage(page + 1)}
      >
        {t("common:ui.pagination.next")}
      </Button>
    </nav>
  )
}
