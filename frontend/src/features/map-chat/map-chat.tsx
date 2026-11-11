import { type ReactNode, useEffect, useRef } from "react"
import { type ChatContext, chatSessionTitle } from "@/entities/chat"
import { useRegion } from "@/entities/region"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import type { AnalysisOverlay } from "@/shared/api/road-analysis"
import type { RoadSegment } from "@/shared/api/road-graph"
import { useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, Button, ChatComposer, Icon, ScrollArea, Tooltip } from "@/shared/ui"
import { ChatAnswer } from "./chat-answer"
import { chatErrorKey, chatStatusKey } from "./chat-copy"
import { ChatEmpty, ChatFollowUp } from "./chat-prompts"
import { ChatRegion } from "./chat-region"
import styles from "./map-chat.module.css"
import { useChatScroll } from "./scroll/use-chat-scroll"
import { SelectedRoads } from "./selected-roads"
import { ChatStorageNotice } from "./sessions/chat-storage-notice"
import { useMapChat } from "./use-map-chat"
import { useRoadPrompt } from "./use-road-prompt"

export interface MapChatProps {
  readonly onSessionChange?: (() => void) | undefined
  readonly onCalculation?: CalculationHandler | undefined
  readonly onScenario?: ((jobId: string) => void) | undefined
  readonly onAnalysisOverlay?: ((overlay: AnalysisOverlay) => void) | undefined
  readonly context: ChatContext
  readonly selection: string | null
  readonly regionCard: (id: string) => ReactNode
  readonly roads: readonly RoadSegment[]
  readonly onClearRoads: () => void
  readonly onMapCommand: MapCommandHandler
}

export function MapChat({
  context,
  selection,
  regionCard,
  roads,
  onClearRoads,
  onMapCommand,
  onCalculation,
  onScenario,
  onAnalysisOverlay,
  onSessionChange,
}: MapChatProps) {
  const { t } = useTranslation()
  const chat = useMapChat(
    { ...context, selected_roads: roads.map(({ way_id, name }) => ({ way_id, name })) },
    onMapCommand,
  )
  useRoadPrompt(roads, chat.draft, chat.setDraft)
  const region = useRegion(context.region_id ?? "", context.season ?? "summer")
  const regionName = regionLabel(context.region_id, region.data, t)
  const active = chat.sessions.find((session) => session.id === chat.sessionId)
  const threadTitle = (active ? chatSessionTitle(active) : "") || t("chat:new")
  const tail = chat.messages.at(-1)
  const { scroll, follow, scrollProps } = useChatScroll(tail)
  const lastRegion = chat.messages.findLast((message) => message.region !== undefined)
  const talked = chat.messages.some((message) => message.region === undefined)
  const postRegion = useRef(chat.postRegion)
  postRegion.current = chat.postRegion
  const posted = useRef<string | null | undefined>(undefined)
  useEffect(() => {
    if (posted.current === selection) return
    posted.current = selection
    if (!selection) return
    follow.current = true
    postRegion.current(selection)
  }, [selection, follow])
  const startNew = () => {
    follow.current = true
    onSessionChange?.()
    chat.newSession()
  }
  const send = (prompt?: string) => {
    follow.current = true
    chat.send(prompt)
  }

  return (
    <aside className={styles.panel} aria-label={t("chat:panelLabel")}>
      <div className={styles.chat}>
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
          {...scrollProps}
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
            {chat.messages.map((message, index) =>
              message.region === undefined ? (
                <ChatAnswer
                  key={message.id}
                  message={message}
                  showSources={chat.messages[index - 1]?.content === t("chat:showSources")}
                  onCommentary={chat.saveCommentary}
                  autoFocus={chat.busy && message.id === tail?.id}
                  onCalculation={onCalculation}
                  onScenario={onScenario}
                  onAnalysisOverlay={onAnalysisOverlay}
                  onMapCommand={onMapCommand}
                />
              ) : (
                <ChatRegion
                  key={message.id}
                  card={regionCard(message.region)}
                  current={message.id === lastRegion?.id && message.region === selection}
                  busy={chat.busy}
                  onAsk={send}
                />
              ),
            )}
            <ChatFollowUp
              messages={chat.messages}
              busy={chat.busy}
              error={chat.error}
              onAsk={send}
            />
            {talked && !chat.error && chat.status !== "done" ? (
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
                <SelectedRoads roads={roads} onClear={onClearRoads} />
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
