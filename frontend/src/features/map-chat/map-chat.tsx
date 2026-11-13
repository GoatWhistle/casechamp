import { type ChatContext, chatSessionTitle } from "@/entities/chat"
import { useRegion } from "@/entities/region"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { useTranslation } from "@/shared/i18n"
import { Swap } from "@/shared/motion"
import { Banner, Button, ChatComposer, Icon, ScrollArea, ThinkingDots, Tooltip } from "@/shared/ui"
import { ownedResults } from "./calculation/owned-results"
import { ChatAnswer } from "./chat-answer"
import { chatErrorKey, chatStatusKey } from "./chat-copy"
import { ChatEmpty } from "./chat-empty"
import styles from "./map-chat.module.css"
import { useChatScroll } from "./scroll/use-chat-scroll"
import { ChatStorageNotice } from "./sessions/chat-storage-notice"
import { useMapChat } from "./use-map-chat"

export interface MapChatProps {
  readonly onSessionChange?: (() => void) | undefined
  readonly onCalculation?: CalculationHandler | undefined
  readonly context: ChatContext
  readonly onMapCommand: MapCommandHandler
}

export function MapChat({ context, onMapCommand, onCalculation, onSessionChange }: MapChatProps) {
  const { t } = useTranslation()
  const chat = useMapChat(context, onMapCommand)
  const region = useRegion(context.region_id ?? "", context.season ?? "summer")
  const regionName = regionLabel(context.region_id, region.data, t)
  const active = chat.sessions.find((session) => session.id === chat.sessionId)
  const threadTitle = (active ? chatSessionTitle(active) : "") || t("chat:new")
  const tail = chat.messages.at(-1)
  const { scroll, follow, scrollProps } = useChatScroll(tail)
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
            {tail && chat.busy && !chat.error ? (
              <p role="status" className={styles.status}>
                <ThinkingDots />
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
