import { isChatAnalysis } from "./chat-analysis"
import { isChatChart, isChatTable } from "./chat-artifacts"
import { isChatCalculation } from "./chat-calculation"
import { isChatMapCommand } from "./chat-map"
import { isChatScenario } from "./chat-scenario"
import { ApiError, api, codeOf, SERVER_UNAVAILABLE, UNEXPECTED } from "./client"
import { isStressJob, isStressRoute } from "./road-stress"
import type { components } from "./schema.gen"
import { isTrafficJob, type TrafficJob } from "./traffic"

type ChatRequest = components["schemas"]["ChatInput"]
export type ChatInput = Omit<ChatRequest, "title_requested"> &
  Partial<Pick<ChatRequest, "title_requested">>
export type ChatContext = components["schemas"]["ChatContextInput"]
export type ChatStreamEvent = Omit<components["schemas"]["ChatStreamEvent"], "traffic"> & {
  traffic?: TrafficJob | null
}

const ARTIFACTS: Record<string, (value: unknown) => boolean> = {
  stress_test: isStressJob,
  traffic: isTrafficJob,
  table: isChatTable,
  chart: isChatChart,
  map: isChatMapCommand,
  calculation: isChatCalculation,
  analysis: isChatAnalysis,
  scenario: isChatScenario,
}

function httpErrorCode(status: number, body: unknown): string {
  const code = codeOf(body)
  if (code !== UNEXPECTED && code !== SERVER_UNAVAILABLE) return code
  if (status === 429) return "chat_limit"
  if (status >= 500 || code === SERVER_UNAVAILABLE) return "chat_connection_error"
  return code
}

function parseEvent(line: string): ChatStreamEvent {
  const value: unknown = JSON.parse(line)
  if (
    typeof value !== "object" ||
    value === null ||
    !("type" in value) ||
    ![
      "status",
      "delta",
      "done",
      "error",
      "table",
      "chart",
      "map",
      "calculation",
      "analysis",
      "stress_test",
      "scenario",
      "title",
      "traffic",
    ].includes(String(value.type)) ||
    !("text" in value) ||
    typeof value.text !== "string" ||
    !("code" in value) ||
    typeof value.code !== "string"
  )
    throw new ApiError(502, "chat_stream_error")
  const artifact = value as Record<string, unknown>
  if (value.type === "title" && (!value.text.trim() || value.text.length > 80))
    throw new ApiError(502, "chat_stream_error")
  const validate = ARTIFACTS[String(value.type)]
  if (validate && !validate(artifact[String(value.type)]))
    throw new ApiError(502, "chat_stream_error")
  if (artifact.stress_route != null && !isStressRoute(artifact.stress_route))
    throw new ApiError(502, "chat_stream_error")
  return value as ChatStreamEvent
}

export async function streamChat(
  body: ChatInput,
  signal: AbortSignal,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<void> {
  const endpoint = body.calculation_review ? "/api/v1/chat/calculation-review" : "/api/v1/chat"
  const { data, response, error } = await api.POST(endpoint, {
    body: { ...body, title_requested: body.title_requested ?? false },
    signal,
    parseAs: "stream",
  })
  if (!response.ok) throw new ApiError(response.status, httpErrorCode(response.status, error))
  if (!data) throw new ApiError(502, "chat_stream_error")
  const reader = data.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let complete = false
  const consume = (line: string) => {
    if (!line.trim()) return
    const event = parseEvent(line)
    if (event.type === "error") throw new ApiError(502, event.code)
    if (event.type === "done") complete = true
    onEvent(event)
  }
  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      const lines = buffer.split("\n")
      buffer = lines.pop() ?? ""
      for (const line of lines) consume(line)
      if (buffer.length > 2000000) throw new ApiError(502, "chat_stream_error")
      if (done) break
    }
    consume(buffer)
    if (!complete) throw new ApiError(502, "chat_stream_error")
  } finally {
    await reader.cancel().catch(() => undefined)
    reader.releaseLock()
  }
}
