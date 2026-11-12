import { type ReactNode, useId, useRef, useState } from "react"
import { useTranslation } from "@/shared/i18n"
import { usePresence } from "@/shared/motion"
import { Button, ScrollArea } from "@/shared/ui"
import styles from "./municipality-index-card.module.css"

export function MunicipalityCardFrame({
  name,
  onClear,
  children,
}: {
  readonly name: string
  readonly onClear: () => void
  readonly children: ReactNode
}) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(true)
  const presence = usePresence(open, "--dur-fast-exit")
  const id = useId()
  const toggle = useRef<HTMLButtonElement>(null)
  return (
    <section
      className={styles.panel}
      data-collapsed={!open || undefined}
      aria-label={t("map:municipalCard.label", { name })}
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          setOpen(false)
          toggle.current?.focus({ preventScroll: true })
        }
      }}
    >
      <div className={styles.header}>
        <Button
          ref={toggle}
          variant="ghost"
          wrap
          className={styles.heading}
          icon={open ? "minus" : "plus"}
          aria-expanded={open}
          aria-controls={presence.mounted ? id : undefined}
          aria-label={t(open ? "map:municipalCard.collapse" : "map:municipalCard.restore", {
            name,
          })}
          onClick={() => setOpen(!open)}
        >
          <span className={styles.name}>{name}</span>
        </Button>
        <Button
          variant="ghost"
          icon="x"
          aria-label={t("map:municipalCard.clear")}
          onClick={onClear}
        >
          {null}
        </Button>
      </div>
      {presence.mounted ? (
        <ScrollArea
          id={id}
          label={t("map:municipalCard.details")}
          className={styles.body}
          inert={!open}
          data-state={presence.state}
          onTransitionEnd={presence.onTransitionEnd}
        >
          {children}
        </ScrollArea>
      ) : null}
    </section>
  )
}
