import type { AnalysisCommentary } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { useTranslation } from "@/shared/i18n"
import { Button, ChatMessage, Disclosure } from "@/shared/ui"
import { ChatFollowups } from "./calculation/chat-followups"
import { ChatResultMap } from "./calculation/chat-result-map"
import styles from "./chat-answer.module.css"
import { chatStatusKey } from "./chat-copy"
import type { ChatEntry } from "./use-map-chat"

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
      text={message.content}
      label={t(`chat:roles.${message.role}`)}
      footer={
        message.complete ? (
          <>
            <div className={styles.actions}>
              {message.steps.length ? (
                <Disclosure
                  className={styles.steps}
                  title={t("chat:steps", { count: message.steps.length })}
                >
                  <ol>
                    {message.steps.map((step) => (
                      <li key={step}>{t(chatStatusKey(step))}</li>
                    ))}
                  </ol>
                </Disclosure>
              ) : null}
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
            {message.complete ? (
              <ChatFollowups
                message={message}
                onCalculation={onCalculation}
                autoReview={autoReview}
                onCommentary={onCommentary}
              />
            ) : null}
          </>
        ) : null
      }
    ></ChatMessage>
  )
}
