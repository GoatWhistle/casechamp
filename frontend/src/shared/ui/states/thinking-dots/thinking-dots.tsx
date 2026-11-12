import styles from "./thinking-dots.module.css"

export function ThinkingDots() {
  return (
    <span className={styles.dots} aria-hidden="true">
      <span className={styles.dot} />
      <span className={styles.dot} />
      <span className={styles.dot} />
    </span>
  )
}
