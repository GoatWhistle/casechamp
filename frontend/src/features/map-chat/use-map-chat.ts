import { useEffect, useRef } from "react"
import {
  type AnalysisCommentary,
  type ChatContext,
  type ChatEntry,
  type ChatInput,
  chatSessionBusy,
  createChatId,
  useChatSessions,
  useChatStream,
} from "@/entities/chat"
import { isApiError } from "@/shared/api"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { clearTrafficView } from "@/shared/hooks/use-traffic-view"
import { applyMapEvent, streamStatus, updateChatRows } from "./chat-events"
import { historyOf } from "./chat-history"

export type { ChatEntry } from "@/entities/chat"

export function useMapChat(context: ChatContext, onMapCommand: MapCommandHandler) {
  const archive = useChatSessions()
  const session = archive.active
  const { update } = archive
  const mapHandler = useRef(onMapCommand)
  mapHandler.current = onMapCommand
  const activeId = useRef(session.id)
  activeId.current = session.id
  const controllers = useRef(new Map<string, AbortController>())
  const requests = useRef(new Map<string, ChatInput>())
  const mutation = useChatStream()
  useEffect(() => {
    const running = controllers.current
    return () => {
      for (const controller of running.values()) controller.abort()
    }
  }, [])

  const run = async (body: ChatInput, previous: ChatEntry[]) => {
    const sessionId = session.id
    if (controllers.current.has(sessionId)) return
    const abort = new AbortController()
    const request = {
      ...body,
      title_requested: !session.title && !previous.some((message) => message.role === "user"),
    }
    controllers.current.set(sessionId, abort)
    requests.current.set(sessionId, request)
    const id = createChatId()
    update(sessionId, (current) => ({
      ...current,
      draft: "",
      error: null,
      status: "connecting",
      messages: [
        ...previous,
        {
          id: createChatId(),
          role: "user",
          content: body.prompt,
          complete: true,
          steps: [],
          tables: [],
          charts: [],
          mapCommands: [],
        },
        {
          id,
          role: "assistant",
          content: "",
          complete: false,
          steps: [],
          tables: [],
          charts: [],
          mapCommands: [],
        },
      ],
    }))
    try {
      await mutation.mutateAsync({
        body: request,
        signal: abort.signal,
        onEvent: (event) => {
          if (abort.signal.aborted) return
          applyMapEvent(event, activeId.current === sessionId, mapHandler.current)
          update(sessionId, (current) => ({
            ...current,
            ...(event.type === "title" && request.title_requested && !current.title
              ? { title: event.text?.trim() ?? "" }
              : {}),
            status: streamStatus(current.status, event),
            messages: updateChatRows(current.messages, id, event),
          }))
        },
      })
    } catch (failure) {
      update(sessionId, (current) => ({
        ...current,
        status: abort.signal.aborted ? "stopped" : "error",
        error: abort.signal.aborted
          ? null
          : isApiError(failure)
            ? failure.code
            : "chat_connection_error",
      }))
    } finally {
      controllers.current.delete(sessionId)
    }
  }
  const send = (text = session.draft) => {
    const prompt = text.trim()
    if (!prompt || prompt.length > 4000) return
    void run({ prompt, history: historyOf(session.messages), context }, session.messages)
  }
  const retry = () => {
    const prompt = session.messages.at(-2)?.content
    if (!prompt) return
    const previous = session.messages.slice(0, -2)
    const body = requests.current.get(session.id) ?? {
      prompt,
      history: historyOf(previous),
      context,
    }
    void run(body, previous)
  }
  const saveCommentary = (messageId: string, analysisId: string, value: AnalysisCommentary) => {
    update(session.id, (current) => ({
      ...current,
      messages: current.messages.map((row) =>
        row.id === messageId
          ? {
              ...row,
              ...(analysisId.startsWith("calculation:") && value.complete
                ? { reviewPending: false }
                : {}),
              commentaries: { ...row.commentaries, [analysisId]: value },
            }
          : row,
      ),
    }))
  }
  return {
    draft: session.draft,
    setDraft: (draft: string) => update(session.id, (current) => ({ ...current, draft })),
    messages: session.messages,
    status: session.status,
    error: session.error,
    sessionId: session.id,
    sessions: archive.sessions,
    selectSession: (id: string) => {
      clearTrafficView()
      archive.select(id)
    },
    newSession: () => {
      clearTrafficView()
      archive.create()
    },
    deleteSession: (id: string) => {
      controllers.current.get(id)?.abort()
      requests.current.delete(id)
      archive.remove(id)
    },
    storageIssue: archive.storageIssue,
    retrySave: archive.save,
    saveCommentary,
    send,
    retry,
    busy: chatSessionBusy(session.status),
    stop: () => controllers.current.get(session.id)?.abort(),
  }
}
