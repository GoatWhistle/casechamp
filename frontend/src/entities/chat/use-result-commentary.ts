import { type QueryClient, useQueryClient } from "@tanstack/react-query"
import { useCallback, useEffect, useRef, useSyncExternalStore } from "react"
import { isApiError } from "@/shared/api"
import type { ChatInput } from "@/shared/api/chat-stream"
import { useChatStream } from "./chat.queries"
import type { AnalysisCommentary } from "./chat-session"

interface ReviewEntry {
  value: AnalysisCommentary
  running: boolean
  listeners: Set<() => void>
}
const EMPTY: AnalysisCommentary = { revision: "", text: "", complete: false, error: null }
const ledgers = new WeakMap<QueryClient, Map<string, ReviewEntry>>()

function reviewEntry(
  client: QueryClient,
  key: string,
  revision: string,
  saved?: AnalysisCommentary,
) {
  let ledger = ledgers.get(client)
  if (!ledger) {
    ledger = new Map()
    ledgers.set(client, ledger)
  }
  let entry = ledger.get(key)
  if (!entry) {
    const value =
      saved?.revision === revision
        ? { ...saved, error: saved.complete ? null : (saved.error ?? "chat_stream_error") }
        : { ...EMPTY, revision }
    entry = { value, running: false, listeners: new Set() }
    ledger.set(key, entry)
  }
  return entry
}

function publish(entry: ReviewEntry, value: AnalysisCommentary) {
  entry.value = value
  for (const listener of entry.listeners) listener()
}

export function useResultCommentary(
  id: string,
  revision: string | null,
  request: ChatInput,
  saved?: AnalysisCommentary | undefined,
  onChange?: ((value: AnalysisCommentary) => void) | undefined,
  autoStart = true,
) {
  const client = useQueryClient()
  const entry = revision === null ? null : reviewEntry(client, `${id}:${revision}`, revision, saved)
  const subscribe = useCallback(
    (listener: () => void) => {
      entry?.listeners.add(listener)
      return () => {
        entry?.listeners.delete(listener)
      }
    },
    [entry],
  )
  const snapshot = useCallback(() => entry?.value ?? EMPTY, [entry])
  const value = useSyncExternalStore(subscribe, snapshot, snapshot)
  const requestRef = useRef(request)
  requestRef.current = request
  const changeRef = useRef(onChange)
  changeRef.current = onChange
  const { mutateAsync } = useChatStream()
  useEffect(() => {
    if (!autoStart || !entry || entry.running || value.complete || value.error) return
    entry.running = true
    const update = (next: AnalysisCommentary) => {
      publish(entry, next)
      changeRef.current?.(next)
    }
    update(entry.value)
    void mutateAsync({
      body: requestRef.current,
      signal: new AbortController().signal,
      onEvent: (event) => {
        if (event.type === "delta")
          update({ ...entry.value, text: entry.value.text + (event.text ?? "") })
        if (event.type === "table" && event.table)
          update({
            ...entry.value,
            tables: [
              ...(entry.value.tables ?? []).filter((table) => table.id !== event.table?.id),
              event.table,
            ],
          })
        if (event.type === "done") update({ ...entry.value, complete: true })
      },
    })
      .catch((failure: unknown) => {
        update({
          ...entry.value,
          error: isApiError(failure) ? failure.code : "chat_connection_error",
        })
      })
      .finally(() => {
        entry.running = false
      })
  }, [entry, mutateAsync, value, autoStart])
  useEffect(() => {
    if (value.revision && (autoStart || value.complete || value.error)) changeRef.current?.(value)
  }, [value, autoStart])
  return {
    ...value,
    pending: entry?.running ?? false,
    retry: () => {
      if (!entry || entry.running) return
      publish(entry, { ...EMPTY, revision: entry.value.revision })
    },
  }
}
