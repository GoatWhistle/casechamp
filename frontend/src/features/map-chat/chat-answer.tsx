import type { AnalysisCommentary } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { useTranslation } from "@/shared/i18n"
import { Button, ChatMessage } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import { ChatFollowups } from "./calculation/chat-followups"
import { ChatResultMap } from "./calculation/chat-result-map"
import styles from "./chat-answer.module.css"
import type { ChatEntry } from "./use-map-chat"

function ChatAuthor() {
  const { t } = useTranslation()
  return (
    <>
      <span className={styles.avatar}>
        <BrandMark kind="symbol" tone="inverse" size="fill" rings={0} decorative />
      </span>
      {t("chat:roles.assistant")}
    </>
  )
}

export function ChatAnswer({
  message,
  autoReview = true,
  onCommentary,
  onMapCommand,
  onCalculation,
}: {
  readonly autoFocus?: boolean
  readonly autoReview?: boolean
  readonly onCommentary?:
    | ((messageId: string, analysisId: string, value: AnalysisCommentary) => void)
    | undefined
  readonly onCalculation?: CalculationHandler | undefined
  readonly message: ChatEntry
  readonly onMapCommand: MapCommandHandler
}) {
  const { t } = useTranslation()
  const hasCalculation = Boolean(message.calculations?.length || message.stressTests?.length)
  return (
    <ChatMessage
      speaker={message.role}
      author={message.role === "assistant" ? <ChatAuthor /> : undefined}
      text={message.content}
      label={t(`chat:roles.${message.role}`)}
      footer={
        message.complete ? (
          <>
            {message.complete ? (
              <ChatFollowups
                message={message}
                onCalculation={onCalculation}
                autoReview={autoReview}
                onCommentary={onCommentary}
              />
            ) : null}
            <div className={styles.actions}>
              {message.calculations?.map((calculation) => (
                <ChatResultMap
                  key={calculation.corridor.id}
                  message={{ ...message, calculations: [calculation], stressTests: [] }}
                  onCalculation={onCalculation}
                  autoFocus={false}
                />
              ))}
              {!hasCalculation &&
                message.mapCommands.map((command) => (
                  <Button
                    key={JSON.stringify(command)}
                    size="compact"
                    className={styles.action}
                    aria-label={t(`chat:mapActions.${command.action}`)}
                    variant="ghost"
                    icon="map"
                    onClick={() => onMapCommand(command)}
                  >
                    {t(`chat:mapActions.${command.action}`)}
                  </Button>
                ))}
            </div>
          </>
        ) : null
      }
    ></ChatMessage>
  )
}
