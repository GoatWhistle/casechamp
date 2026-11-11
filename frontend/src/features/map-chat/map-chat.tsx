import { type ReactNode, useEffect, useId, useRef, useState } from "react"
import { useSearchParams } from "react-router"
import { type ChatContext, chatSessionTitle } from "@/entities/chat"
import { useRegion } from "@/entities/region"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, Button, ChatComposer, Icon, ScrollArea, Tabs, Tooltip } from "@/shared/ui"
import { ownedResults } from "./calculation/owned-results"
import { ChatAnswer } from "./chat-answer"
import { chatErrorKey, chatStatusKey } from "./chat-copy"
import { ChatEmpty } from "./chat-empty"
import styles from "./map-chat.module.css"
import { ChatStorageNotice } from "./sessions/chat-storage-notice"
import { useMapChat } from "./use-map-chat"

export interface MapChatProps {
  readonly onSessionChange?: (() => void) | undefined
  readonly onCalculation?: CalculationHandler | undefined
  readonly context: ChatContext
  readonly summary: ReactNode
  readonly scenario?: ReactNode
  readonly onMapCommand: MapCommandHandler
}

export function MapChat({
  context,
  summary,
  scenario,
  onMapCommand,
  onCalculation,
  onSessionChange,
}: MapChatProps) {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState<"chat" | "summary" | "scenario">(initialTab(searchParams))
  const chat = useMapChat(context, onMapCommand)
  const region = useRegion(context.region_id ?? "", context.season ?? "summer")
  const regionName = regionLabel(context.region_id, region.data, t)
  const active = chat.sessions.find((session) => session.id === chat.sessionId)
  const threadTitle = (active ? chatSessionTitle(active) : "") || t("chat:new")
  const titleId = useId()
  const scroll = useRef<HTMLDivElement>(null)
  const follow = useRef(true)
  const tail = chat.messages.at(-1)
  useEffect(() => {
    const node = scroll.current
    if (tail === undefined || !node) return
    const sync = () => {
      if (follow.current) node.scrollTop = node.scrollHeight
    }
    sync()
    const observer = new ResizeObserver(sync)
    for (const child of node.children) observer.observe(child)
    return () => observer.disconnect()
  }, [tail])
  const startNew = () => {
    follow.current = true
    onSessionChange?.()
    chat.newSession()
    setTab("chat")
  }
  const send = (prompt?: string) => {
    follow.current = true
    chat.send(prompt)
  }

  return (
    <aside className={styles.panel} aria-label={t("chat:panelLabel")}>
      <div className={styles.bar}>
        <Tabs
          label={t("chat:panelLabel")}
          value={tab}
          onChange={setTab}
          className={styles.tabs}
          controls={{
            chat: `${titleId}chat`,
            summary: `${titleId}summary`,
            scenario: `${titleId}scenario`,
          }}
          items={[
            { value: "chat", label: t("chat:tab"), icon: "chat" },
            { value: "summary", label: t("chat:summary"), icon: "overview" },
            { value: "scenario", label: t("graph:tab"), icon: "whatif" },
          ]}
        />
      </div>
      <div
        id={`${titleId}scenario`}
        role="tabpanel"
        aria-label={t("graph:tab")}
        className={styles.summary}
        data-hidden={tab !== "scenario" || undefined}
      >
        {scenario}
      </div>
      <div
        id={`${titleId}summary`}
        role="tabpanel"
        aria-label={t("chat:summary")}
        className={styles.summary}
        data-hidden={tab !== "summary" || undefined}
      >
        {summary}
      </div>
      <div
        id={`${titleId}chat`}
        role="tabpanel"
        aria-label={t("chat:tab")}
        className={styles.chat}
        data-hidden={tab !== "chat" || undefined}
      >
        {chat.messages.length > 0 ? (
          <div className={styles.thread}>
            <p className={styles.threadTitle}>{threadTitle}</p>
            <Tooltip content={t("chat:new")}>
              <Button
                variant="ghost"
                size="compact"
                icon="plus"
                aria-label={t("chat:new")}
                onClick={startNew}
              >
                {null}
              </Button>
            </Tooltip>
          </div>
        ) : null}
        <ScrollArea
          ref={scroll}
          className={styles.messages}
          label={t("chat:history")}
          onScroll={() => {
            const node = scroll.current
            if (node) follow.current = node.scrollHeight - node.scrollTop - node.clientHeight < 80
          }}
        >
          <Swap swapKey={chat.sessionId} as="div" className={styles.swap}>
            {chat.messages.length === 0 ? (
              <ChatEmpty
                sessions={chat.sessions}
                activeId={chat.sessionId}
                onAsk={send}
                onSelect={(id) => {
                  follow.current = true
                  if (id !== chat.sessionId) onSessionChange?.()
                  chat.selectSession(id)
                }}
                onDelete={(id) => {
                  if (id === chat.sessionId) onSessionChange?.()
                  chat.deleteSession(id)
                }}
              />
            ) : null}
            {chat.messages.map((message, index) => (
              <ChatAnswer
                key={message.id}
                message={ownedResults(chat.messages, index)}
                onCommentary={chat.saveCommentary}
                autoReview={message.reviewPending ?? message.id === tail?.id}
                autoFocus={chat.busy && message.id === tail?.id}
                onCalculation={onCalculation}
                onMapCommand={onMapCommand}
              />
            ))}
            {chat.messages.length &&
            !chat.error &&
            !tail?.calculations?.length &&
            !tail?.stressTests?.length &&
            !tail?.scenarios?.length &&
            !tail?.analyses?.length ? (
              <p role="status" className={styles.status}>
                <Icon name={statusIcon(chat.busy, Boolean(chat.error))} size="sm" />
                {t(chatStatusKey(chat.status))}
              </p>
            ) : null}
          </Swap>
        </ScrollArea>
        <div className={styles.footer}>
          <ChatStorageNotice issue={chat.storageIssue} onRetry={chat.retrySave} />
          {chat.error ? (
            <Banner
              tone="danger"
              announce
              title={t(chatErrorKey(chat.error))}
              action={
                <Button icon="retry" variant="ghost" onClick={chat.retry}>
                  {t("chat:retry")}
                </Button>
              }
            />
          ) : null}
          <ChatComposer
            context={
              <>
                <span className={styles.contextItem}>
                  <Icon name="map" size="sm" />
                  {regionName}
                </span>
                <span className={styles.contextItem}>
                  <Icon name={context.season === "winter" ? "snowflake" : "sun"} size="sm" />
                  {t(`data:season.${context.season ?? "summer"}`)}
                </span>
              </>
            }
            value={chat.draft}
            onValue={chat.setDraft}
            pending={chat.busy}
            onSend={() => send()}
            onStop={chat.stop}
            label={t("chat:prompt")}
            placeholder={t("chat:placeholder")}
            sendLabel={t("chat:send")}
            stopLabel={t("chat:stop")}
          />
        </div>
      </div>
    </aside>
  )
}

function regionLabel(
  id: string | null | undefined,
  data: { readonly id: string; readonly name: string } | undefined,
  t: ReturnType<typeof useTranslation>["t"],
): string {
  if (!id) return t("chat:allRegions")
  return data?.id === id ? data.name : t("common:state.loading")
}

function statusIcon(busy: boolean, failed: boolean): "neutral" | "error" | "check" {
  if (busy) return "neutral"
  return failed ? "error" : "check"
}

function initialTab(params: URLSearchParams): "chat" | "scenario" {
  return params.has("analysis") || params.get("panel") === "scenario" ? "scenario" : "chat"
}
