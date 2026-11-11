import styles from "./source-catalog.module.css"

const URL_PATTERN = /(https?:\/\/[^\s)]+)/

export function SourceNote({ text }: { readonly text: string }) {
  let offset = 0
  const parts = text.split(URL_PATTERN).map((part) => {
    const start = offset
    offset += part.length
    return { part, start, link: URL_PATTERN.test(part) }
  })
  return (
    <span className={styles.note}>
      {parts.map(({ part, start, link }) =>
        link ? (
          <a key={start} href={part} target="_blank" rel="noreferrer">
            {part}
          </a>
        ) : (
          <span key={start}>{part}</span>
        ),
      )}
    </span>
  )
}
