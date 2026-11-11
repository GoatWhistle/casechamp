import { type AnalysisCommentary, useCalculationTables } from "@/entities/chat"
import { useTranslation } from "@/shared/i18n"
import { Button, ChatMessage } from "@/shared/ui"
import { ChatArtifacts } from "../chat-artifacts"

export function ChatResultEvidence({
  review,
  scenarioIds,
  stressIds,
  finished,
}: {
  readonly review: AnalysisCommentary
  readonly scenarioIds: readonly string[]
  readonly stressIds: readonly string[]
  readonly finished: boolean
}) {
  const { t } = useTranslation()
  const legacy =
    review.complete &&
    !review.tables?.length &&
    /\n[ \t]*\|?[ \t]*:?-{3,}:?[ \t]*\|/.test(review.text)
  const restored = useCalculationTables(scenarioIds, stressIds, legacy && finished)
  const tables = review.tables ?? restored.data
  return (
    <>
      {tables?.length ? <ChatArtifacts tables={tables} charts={[]} /> : null}
      {review.text && !legacy ? (
        <ChatMessage speaker="assistant" text={review.text} label={t("chat:analysis.commentary")} />
      ) : null}
      {legacy && restored.isError ? (
        <p role="alert">
          {t("chat:calculationRun.requestError")}{" "}
          <Button variant="ghost" icon="retry" onClick={() => void restored.refetch()}>
            {t("chat:retry")}
          </Button>
        </p>
      ) : null}
    </>
  )
}
