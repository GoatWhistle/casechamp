import type { AnalysisCommentary } from "./chat-session"
import { useResultCommentary } from "./use-result-commentary"

export function useAnalysisCommentary(
  analysisId: string,
  revision: string | null,
  saved?: AnalysisCommentary | undefined,
  onChange?: ((value: AnalysisCommentary) => void) | undefined,
  autoStart = true,
) {
  return useResultCommentary(
    analysisId,
    revision,
    { prompt: "Review the completed analysis", analysis_id: analysisId },
    saved,
    onChange,
    autoStart,
  )
}
