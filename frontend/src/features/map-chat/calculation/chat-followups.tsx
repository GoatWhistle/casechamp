import { useState } from "react"
import type { AnalysisCommentary, ChatEntry } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import { ChatAnalysisCard } from "../analysis/chat-analysis-card"
import { ChatArtifacts } from "../chat-artifacts"
import { ChatCalculationRun } from "./chat-calculation-run"

export function ChatFollowups({
  message,
  autoReview,
  onCalculation,
  onCommentary,
}: {
  readonly onCalculation?: CalculationHandler | undefined
  readonly message: ChatEntry
  readonly autoReview: boolean
  readonly onCommentary:
    | ((messageId: string, key: string, value: AnalysisCommentary) => void)
    | undefined
}) {
  const [calculationDone, setCalculationDone] = useState(false)
  const [analysisCount, setAnalysisCount] = useState(0)
  const hasCalculation = Boolean(
    message.calculations?.length || message.stressTests?.length || message.scenarios?.length,
  )
  const analyses = message.analyses ?? []
  const ready = !hasCalculation || calculationDone
  return (
    <>
      {hasCalculation ? (
        <ChatCalculationRun
          message={message}
          onCalculation={onCalculation}
          autoReview={autoReview}
          onCommentary={onCommentary}
          onSettled={() => setCalculationDone(true)}
        />
      ) : null}
      {ready
        ? analyses
            .slice(0, analysisCount + 1)
            .map((analysis, index) => (
              <ChatAnalysisCard
                key={analysis.id}
                analysis={analysis}
                autoReview={autoReview}
                commentary={message.commentaries?.[analysis.id]}
                onCommentary={(value) => onCommentary?.(message.id, analysis.id, value)}
                onSettled={() => setAnalysisCount((count) => Math.max(count, index + 1))}
              />
            ))
        : null}
      {ready && analysisCount >= analyses.length ? (
        <ChatArtifacts tables={message.tables} charts={message.charts} />
      ) : null}
    </>
  )
}
