import { clsx } from "clsx"
import type { ButtonHTMLAttributes, ReactNode, Ref } from "react"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./row-button.module.css"

export interface RowButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children" | "type"> {
  readonly icon?: IconName | undefined
  readonly label: ReactNode
  readonly detail?: ReactNode
  readonly meta?: ReactNode
  readonly pressed?: boolean | undefined
  readonly current?: boolean | undefined
  readonly chevron?: boolean | undefined
  readonly ref?: Ref<HTMLButtonElement> | undefined
}

export function RowButton({
  icon,
  label,
  detail,
  meta,
  pressed,
  current,
  chevron = false,
  className,
  ...rest
}: RowButtonProps) {
  return (
    <button
      {...rest}
      type="button"
      aria-pressed={pressed}
      aria-current={current ? "true" : undefined}
      className={clsx(styles.row, className)}
      data-lead={icon === undefined ? undefined : true}
    >
      {icon === undefined ? null : (
        <span className={styles.lead} aria-hidden="true">
          <Icon name={icon} size="sm" className={styles.glyph} />
          {pressed === undefined ? null : <Icon name="check" size="sm" className={styles.check} />}
        </span>
      )}
      <span className={styles.text}>
        <span className={styles.label}>{label}</span>
        {detail === undefined ? null : <span className={styles.detail}>{detail}</span>}
      </span>
      {meta === undefined ? null : <span className={styles.meta}>{meta}</span>}
      {chevron ? <Icon name="chevron-right" size="sm" className={styles.chevron} /> : null}
    </button>
  )
}
