import { useMutation, useQuery } from "@tanstack/react-query"
import { api, unwrap } from "@/shared/api"
import { type ChatInput, type ChatStreamEvent, streamChat } from "@/shared/api/chat-stream"

interface ChatTurn {
  readonly body: ChatInput
  readonly signal: AbortSignal
  readonly onEvent: (event: ChatStreamEvent) => void
  readonly onStart?: () => void
}

export function useChatStream() {
  return useMutation({
    scope: { id: "chat-stream" },
    mutationFn: ({ body, signal, onEvent, onStart }: ChatTurn) => {
      signal.throwIfAborted()
      onStart?.()
      return streamChat(body, signal, onEvent)
    },
    retry: false,
  })
}

export function useCalculationTables(
  scenarioIds: readonly string[],
  stressIds: readonly string[],
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["chat-calculation-tables", scenarioIds, stressIds],
    queryFn: ({ signal }) =>
      unwrap(
        api.POST("/api/v1/chat/calculation-tables", {
          signal,
          body: { scenario_ids: [...scenarioIds], stress_ids: [...stressIds] },
        }),
      ),
    enabled,
    staleTime: Number.POSITIVE_INFINITY,
    retry: false,
  })
}
