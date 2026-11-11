import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, render, screen, waitFor } from "@testing-library/react"
import { StrictMode } from "react"
import { afterEach, expect, it, vi } from "vitest"
import type { AnalysisCommentary, ChatEntry } from "@/entities/chat"
import { ChatAnswer } from "@/features/map-chat/chat-answer"
import { streamChat } from "@/shared/api/chat-stream"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/chat.json"

vi.mock("@/shared/api/chat-stream", async (load) => ({
  ...(await load<typeof import("@/shared/api/chat-stream")>()),
  streamChat: vi.fn(),
}))

const corridor = {
  id: "selected",
  scope: "roads",
  road_ref: "Long road inventory",
  origin: "A",
  destination: "B",
  way_ids: [7],
  length_km: 4,
  origin_attachment_km: 0,
  destination_attachment_km: 0,
  regions: [{ id: "1", name: "First" }],
  lines: [
    [
      [40, 44],
      [41, 45],
    ],
  ],
}
const message: ChatEntry = {
  id: "answer",
  role: "assistant",
  complete: true,
  content: "| Region | Job ID |\n| --- | --- |\n| First | private-first |",
  steps: ["calculate_scenario"],
  tables: [],
  charts: [],
  mapCommands: [],
  calculations: [
    { corridor, job_ids: ["private-first"] },
    { corridor: { ...corridor, id: "second" }, job_ids: ["private-second"] },
  ],
}
const clients: QueryClient[] = []
const job = (id: string, status: string) => ({
  id,
  status,
  version: "v",
  completed: 50,
  total: 100,
})
function client(status: string) {
  const cache = new QueryClient({
    defaultOptions: { queries: { staleTime: Infinity, retry: false } },
  })
  for (const id of ["private-first", "private-second"])
    cache.setQueryData(["road-scenario", id], job(id, status))
  clients.push(cache)
  return cache
}
function content(cache: QueryClient, entry = message, onCommentary = vi.fn(), autoReview = true) {
  return (
    <StrictMode>
      <QueryClientProvider client={cache}>
        <LocaleProvider>
          <ChatAnswer
            message={entry}
            onMapCommand={vi.fn()}
            onCommentary={onCommentary}
            autoReview={autoReview}
          />
        </LocaleProvider>
      </QueryClientProvider>
    </StrictMode>
  )
}
afterEach(() => {
  for (const cache of clients.splice(0)) cache.clear()
  vi.resetAllMocks()
})

it("preserves agent Markdown and appends a map action and combined progress bar", () => {
  const view = render(content(client("running")))
  expect(
    screen.getAllByRole("button", {
      name: ru.calculationRun.mapTarget.replace("{{target}}", corridor.road_ref),
    }),
  ).toHaveLength(2)
  expect(screen.getAllByRole("progressbar")).toHaveLength(1)
  expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("50")
  expect(screen.getByRole("table")).toBeTruthy()
  expect(screen.getByText("private-first")).toBeTruthy()
  expect(screen.queryByText(corridor.road_ref)).toBeNull()
  expect(streamChat).not.toHaveBeenCalled()
  view.unmount()
})

it("waits for all results then streams a single saved interpretation", async () => {
  vi.mocked(streamChat).mockImplementation(async (_body, _signal, emit) => {
    emit({ type: "delta", text: "**Verified outcome**\n\n- A longer trip", code: "" })
    emit({ type: "done", text: "", code: "" })
  })
  const cache = client("running")
  let saved: AnalysisCommentary | undefined
  let key = ""
  const remember = vi.fn((_message: string, id: string, value: AnalysisCommentary) => {
    saved = value
    key = id
  })
  const view = render(content(cache, message, remember))
  act(() =>
    cache.setQueryData(["road-scenario", "private-first"], job("private-first", "completed")),
  )
  expect(streamChat).not.toHaveBeenCalled()
  act(() =>
    cache.setQueryData(["road-scenario", "private-second"], job("private-second", "completed")),
  )
  await screen.findByText("Verified outcome")
  expect(screen.getByRole("list")).toBeTruthy()
  expect(streamChat).toHaveBeenCalledTimes(1)
  expect(vi.mocked(streamChat).mock.calls[0]?.[0].calculation_review?.scenario_ids).toEqual([
    "private-first",
    "private-second",
  ])
  expect(saved?.complete).toBe(true)
  view.unmount()
  const restored = render(
    content(client("completed"), {
      ...message,
      commentaries: { [key]: saved as AnalysisCommentary },
    }),
  )
  await screen.findByText("Verified outcome")
  expect(streamChat).toHaveBeenCalledTimes(1)
  restored.unmount()
})

it("does not ask for an interpretation when all jobs fail", () => {
  const view = render(content(client("failed")))
  expect(screen.getByText(ru.calculationRun.failed)).toBeTruthy()
  expect(streamChat).not.toHaveBeenCalled()
  view.unmount()
})

it("does not launch new model calls for completed historical messages", () => {
  const view = render(content(client("completed"), message, vi.fn(), false))
  expect(streamChat).not.toHaveBeenCalled()
  view.unmount()
})

it("keeps an interpretation running while the conversation is unmounted", async () => {
  let finish = () => {}
  vi.mocked(streamChat).mockImplementation(
    (_body, signal, emit) =>
      new Promise((resolve) => {
        finish = () => {
          expect(signal.aborted).toBe(false)
          emit({ type: "delta", text: "Background result", code: "" })
          emit({ type: "done", text: "", code: "" })
          resolve()
        }
      }),
  )
  const cache = client("completed")
  const remember = vi.fn()
  const first = render(content(cache, message, remember))
  await waitFor(() => expect(streamChat).toHaveBeenCalledTimes(1))
  first.unmount()
  await act(async () => finish())
  expect(remember.mock.lastCall?.[2].complete).toBe(true)
  const second = render(content(cache))
  await screen.findByText("Background result")
  expect(streamChat).toHaveBeenCalledTimes(1)
  second.unmount()
})

it("keeps the requested scenario order instead of sorting random job IDs", async () => {
  vi.mocked(streamChat).mockImplementation(async (_body, _signal, emit) => {
    emit({ type: "done", text: "", code: "" })
  })
  const view = render(
    content(client("completed"), {
      ...message,
      calculations: [{ corridor, job_ids: ["private-second", "private-first"] }],
    }),
  )
  await waitFor(() => expect(streamChat).toHaveBeenCalledTimes(1))
  expect(vi.mocked(streamChat).mock.calls[0]?.[0].calculation_review?.scenario_ids).toEqual([
    "private-second",
    "private-first",
  ])
  view.unmount()
})
