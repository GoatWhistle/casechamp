import { type QueryClient, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { isApiError } from "@/shared/api"
import { useChatStream } from "./chat.queries"
import type { AnalysisCommentary } from "./chat-session"

const requested = new WeakMap<QueryClient, Map<string, AnalysisCommentary>>()

function requestLedger(client: QueryClient): Map<string, AnalysisCommentary> {
  const known = requested.get(client)
  if (known) return known
  const created = new Map<string, AnalysisCommentary>()
  requested.set(client, created)
  return created
}

export function useAnalysisCommentary(
  analysisId: string,
  revision: string | null,
  saved?: AnalysisCommentary | undefined,
  onChange?: ((value: AnalysisCommentary) => void) | undefined,
) {
  const [text, setText] = useState(saved?.text ?? "")
  const [error, setError] = useState<string | null>(saved?.error ?? null)
  const [complete, setComplete] = useState(saved?.complete ?? false)
  const [attempt, setAttempt] = useState(0)
  const consumed = useRef(0)
  const savedRef = useRef(saved)
  savedRef.current = saved
  const changeRef = useRef(onChange)
  changeRef.current = onChange
  const ledger = requestLedger(useQueryClient())
  const { mutateAsync, isPending } = useChatStream()
  useEffect(() => {
    if (revision === null) return
    const key = `${analysisId}:${revision}`
    const existing = savedRef.current?.revision === revision ? savedRef.current : ledger.get(key)
    if (attempt === consumed.current && existing) {
      setText(existing.text)
      setComplete(existing.complete)
      setError(existing.complete ? null : (existing.error ?? "chat_stream_error"))
      return
    }
    consumed.current = attempt
    const abort = new AbortController()
    let value: AnalysisCommentary = { revision, text: "", complete: false, error: null }
    let started = false
    const publish = (next: AnalysisCommentary) => {
      value = next
      if (started) ledger.set(key, value)
      setText(value.text)
      setComplete(value.complete)
      setError(value.error)
      changeRef.current?.(value)
    }
    publish(value)
    void mutateAsync({
      body: { prompt: "Review the completed analysis", analysis_id: analysisId },
      signal: abort.signal,
      onStart: () => {
        started = true
        ledger.set(key, value)
      },
      onEvent: (event) => {
        if (abort.signal.aborted) return
        if (event.type === "delta") publish({ ...value, text: value.text + (event.text ?? "") })
        if (event.type === "done") publish({ ...value, complete: true })
      },
    }).catch((failure: unknown) => {
      if (!abort.signal.aborted)
        publish({ ...value, error: isApiError(failure) ? failure.code : "chat_connection_error" })
    })
    return () => {
      abort.abort()
      if (value.complete || value.error) return
      value = { ...value, error: "chat_stream_error" }
      if (started) ledger.set(key, value)
      changeRef.current?.(value)
    }
  }, [analysisId, revision, attempt, mutateAsync, ledger])
  return {
    text,
    error,
    complete,
    pending: isPending,
    retry: () => setAttempt((value) => value + 1),
  }
}
