import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, fireEvent, render, screen } from "@testing-library/react"
import { StrictMode } from "react"
import { afterEach, describe, expect, it, vi } from "vitest"
import type { AnalysisCommentary } from "@/entities/chat"
import { ChatAnalysisCard } from "@/features/map-chat/analysis/chat-analysis-card"
import { ApiError } from "@/shared/api"
import { streamChat } from "@/shared/api/chat-stream"
import type { AnalysisJob } from "@/shared/api/road-analysis"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/chat.json"

vi.mock("@/shared/api/chat-stream", async (load) => ({
  ...(await load<typeof import("@/shared/api/chat-stream")>()),
  streamChat: vi.fn(),
}))

const paused: AnalysisJob = {
  id: "analysis-busy",
  region_id: "16",
  region: "Region",
  mode: "criticality",
  percent: 20,
  fingerprint: "snapshot",
  status: "paused",
  stage: "verifying",
  candidates: [],
  results: [],
  failures: [],
  candidate_count: 25,
  batch_target: 10,
  current_way_id: null,
  completed: 10,
  total: 10,
  elapsed_seconds: 1,
  error: null,
  compatible: true,
}

const clients: QueryClient[] = []
function client() {
  const value = new QueryClient({
    defaultOptions: { queries: { staleTime: Infinity, retry: false } },
  })
  clients.push(value)
  return value
}

function card(cache: QueryClient, commentary?: AnalysisCommentary) {
  return (
    <QueryClientProvider client={cache}>
      <LocaleProvider>
        <ChatAnalysisCard analysis={paused} commentary={commentary} />
      </LocaleProvider>
    </QueryClientProvider>
  )
}

const busy = () => Promise.reject(new ApiError(502, "chat_busy"))

afterEach(() => {
  clients.splice(0).forEach((value) => {
    value.clear()
  })
  vi.resetAllMocks()
})

describe("analysis commentary requests", () => {
  it("shows a busy server as a retryable state without asking again on its own", async () => {
    vi.mocked(streamChat).mockImplementation(busy)
    const view = render(card(client()))
    await screen.findByText(ru.errors.busy)
    await act(() => new Promise((resolve) => setTimeout(resolve, 50)))
    expect(streamChat).toHaveBeenCalledTimes(1)
    expect(screen.getByRole("button", { name: ru.retry })).toBeTruthy()
    view.unmount()
  })

  it("does not request the same revision again when the card remounts without saved state", async () => {
    vi.mocked(streamChat).mockImplementation(busy)
    const cache = client()
    const first = render(card(cache))
    await screen.findByText(ru.errors.busy)
    first.unmount()
    const second = render(card(cache))
    await screen.findByRole("button", { name: ru.retry })
    expect(streamChat).toHaveBeenCalledTimes(1)
    second.unmount()
  })

  it("keeps a manual retry to one request when the revision flips afterwards", async () => {
    vi.mocked(streamChat).mockImplementation(busy)
    const cache = client()
    const view = render(card(cache))
    await screen.findByText(ru.errors.busy)
    fireEvent.click(screen.getByRole("button", { name: ru.retry }))
    await screen.findByText(ru.errors.busy)
    expect(streamChat).toHaveBeenCalledTimes(2)
    for (const status of ["running", "paused", "running", "paused"] as const) {
      act(() => cache.setQueryData(["road-analysis", paused.id], { ...paused, status }))
      await act(() => new Promise((resolve) => setTimeout(resolve, 10)))
    }
    await act(() => new Promise((resolve) => setTimeout(resolve, 50)))
    expect(streamChat).toHaveBeenCalledTimes(2)
    view.unmount()
  })

  it("streams one commentary under development double effects", async () => {
    vi.mocked(streamChat).mockImplementation(async (_body, _signal, emit) => {
      emit({ type: "delta", text: "Single commentary", code: "" })
      emit({ type: "done", text: "", code: "" })
    })
    const view = render(<StrictMode>{card(client())}</StrictMode>)
    await screen.findByText("Single commentary")
    expect(streamChat).toHaveBeenCalledTimes(1)
    view.unmount()
  })
})
