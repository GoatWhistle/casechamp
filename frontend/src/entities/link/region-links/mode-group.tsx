import { useState } from "react"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, Disclosure } from "@/shared/ui"
import type { Link, Mode } from "../link.queries"
import { LinkList } from "../link-list/link-list"
import type { ModeShare } from "../link-modes"
import { ModeSwatch } from "../mode-swatch/mode-swatch"
import styles from "./region-links.module.css"

const PREVIEW = 5
const STEP = 20

export interface ModeGroupProps {
  readonly share: ModeShare
  readonly links: readonly Link[]
  readonly defaultOpen: boolean
  readonly onActive: (mode: Mode | null) => void
}

export function ModeGroup({ share, links, defaultOpen, onActive }: ModeGroupProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [shown, setShown] = useState(PREVIEW)
  const rest = links.length - shown
  return (
    <li
      className={styles.group}
      onPointerEnter={(event) => {
        if (event.pointerType === "mouse") onActive(share.mode)
      }}
      onPointerLeave={() => onActive(null)}
      onFocus={() => onActive(share.mode)}
      onBlur={() => onActive(null)}
    >
      <Disclosure
        className={styles.disclosure}
        defaultOpen={defaultOpen}
        title={
          <span className={styles.head}>
            <ModeSwatch mode={share.mode} />
            <span className={styles.name}>{t(`data:mode.${share.mode}`)}</span>
            <span className={styles.count}>{f.integer(share.count)}</span>
          </span>
        }
      >
        <div className={styles.routes}>
          <LinkList rows={links.slice(0, shown)} showMode={false} />
        </div>
        {rest > 0 ? (
          <Button
            variant="ghost"
            size="compact"
            icon="chevron-down"
            className={styles.more}
            onClick={() => setShown(shown + STEP)}
          >
            {t("links:more", { count: Math.min(STEP, rest) })}
          </Button>
        ) : null}
      </Disclosure>
    </li>
  )
}
