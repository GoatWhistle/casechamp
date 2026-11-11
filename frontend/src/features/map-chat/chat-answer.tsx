import type { AnalysisCommentary } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import type { AnalysisOverlay } from "@/shared/api/road-analysis"
import { useTranslation } from "@/shared/i18n"
import { Button, ChatMessage } from "@/shared/ui"
import { ChatAnalysisCard } from "./analysis/chat-analysis-card"
import { ChatArtifacts } from "./chat-artifacts"
import { ChatCalculationCard } from "./chat-calculation-card"
import { ChatScenarioCard } from "./chat-scenario-card"
import { presentMessage } from "./message-presentation"
import type { ChatEntry } from "./use-map-chat"

export function ChatAnswer({
  message,
  showSources = false,
  autoFocus = false,
  onCommentary,
  onMapCommand,
  onCalculation,
  onScenario,
  onAnalysisOverlay,
}: {
  readonly showSources?: boolean
  readonly autoFocus?: boolean
  readonly onCommentary?:
    | ((messageId: string, analysisId: string, value: AnalysisCommentary) => void)
    | undefined
  readonly onCalculation?: CalculationHandler | undefined
  readonly onScenario?: ((jobId: string) => void) | undefined
  readonly onAnalysisOverlay?: ((overlay: AnalysisOverlay) => void) | undefined
  readonly message: ChatEntry
  readonly onMapCommand: MapCommandHandler
}) {
  const { t } = useTranslation()
  const text =
    message.role === "assistant" && !showSources
      ? presentMessage(message.content).text
      : message.content
  return (
    <ChatMessage
      speaker={message.role}
      framed={message.role === "assistant"}
      text={text}
      label={t(`chat:roles.${message.role}`)}
      footer={
        <>
          {message.mapCommands.map((command) => (
            <Button
              key={JSON.stringify(command)}
              variant="ghost"
              icon="map"
              onClick={() => onMapCommand(command)}
            >
              {t(`chat:mapActions.${command.action}`)}
            </Button>
          ))}
          {message.calculations?.map((calculation) => (
            <ChatCalculationCard
              key={calculation.corridor.id}
              calculation={calculation}
              autoFocus={autoFocus}
              onShow={onCalculation}
            />
          ))}
          {message.scenarios?.map((scenario) => (
            <ChatScenarioCard
              key={scenario.job_ids.join("|")}
              scenario={scenario}
              onShow={onScenario}
            />
          ))}
          {message.analyses?.map((analysis) => (
            <ChatAnalysisCard
              key={analysis.id}
              analysis={analysis}
              commentary={message.commentaries?.[analysis.id]}
              onCommentary={(value) => onCommentary?.(message.id, analysis.id, value)}
              onOverlay={onAnalysisOverlay}
            />
          ))}
          <ChatArtifacts
            tables={message.tables}
            charts={message.charts}
            showSources={showSources}
          />
        </>
      }
    />
  )
}
