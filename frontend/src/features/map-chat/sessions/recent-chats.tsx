import { useState } from "react"
import { type ChatSession, chatSessionBusy, chatSessionTitle } from "@/entities/chat"
import { type Formatters, useFormatters, useTranslation } from "@/shared/i18n"
import { Button, Dialog, Tooltip } from "@/shared/ui"
import styles from "./recent-chats.module.css"

export interface RecentChatsProps {
  readonly sessions: readonly ChatSession[]
  readonly activeId: string
  readonly onSelect: (id: string) => void
  readonly onDelete: (id: string) => void
}

const LIMIT = 4

function stamp(value: string | number | Date, f: Formatters): string {
  const date = new Date(value)
  return date.toDateString() === new Date().toDateString() ? f.time(date) : f.date(date)
}

export function RecentChats({ sessions, activeId, onSelect, onDelete }: RecentChatsProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [deleting, setDeleting] = useState<ChatSession | null>(null)
  const [expanded, setExpanded] = useState(false)
  const all = sessions.filter(
    (session) => session.id !== activeId && chatSessionTitle(session) !== "",
  )
  const recent = expanded ? all : all.slice(0, LIMIT)
  if (all.length === 0) return null
  return (
    <section className={styles.recent} aria-label={t("chat:sessions.title")}>
      <p className={styles.heading}>{t("chat:sessions.title")}</p>
      <ul className={styles.list}>
        {recent.map((session) => {
          const title = chatSessionTitle(session)
          return (
            <li key={session.id} className={styles.row}>
              <Button variant="ghost" className={styles.item} onClick={() => onSelect(session.id)}>
                <span className={styles.name}>{title}</span>
                <span className={styles.meta}>
                  {chatSessionBusy(session.status)
                    ? t("chat:sessions.responding")
                    : stamp(session.updatedAt, f)}
                </span>
              </Button>
              <Tooltip content={t("chat:sessions.delete")}>
                <Button
                  variant="ghost"
                  icon="trash"
                  className={styles.delete}
                  aria-label={t("chat:sessions.deleteNamed", { name: title })}
                  onClick={() => setDeleting(session)}
                >
                  {null}
                </Button>
              </Tooltip>
            </li>
          )
        })}
      </ul>
      {recent.length < all.length ? (
        <Button
          variant="ghost"
          size="compact"
          icon="chevron-down"
          className={styles.more}
          onClick={() => setExpanded(true)}
        >
          {t("chat:sessions.showAll", { count: all.length })}
        </Button>
      ) : null}
      <Dialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title={t("chat:sessions.deleteTitle")}
        description={t("chat:sessions.deleteDescription")}
        actions={
          <>
            <Button variant="secondary" onClick={() => setDeleting(null)}>
              {t("chat:sessions.keep")}
            </Button>
            <Button
              variant="danger"
              icon="trash"
              onClick={() => {
                if (deleting) onDelete(deleting.id)
                setDeleting(null)
              }}
            >
              {t("chat:sessions.delete")}
            </Button>
          </>
        }
      >
        <p>{deleting ? chatSessionTitle(deleting) : ""}</p>
      </Dialog>
    </section>
  )
}
