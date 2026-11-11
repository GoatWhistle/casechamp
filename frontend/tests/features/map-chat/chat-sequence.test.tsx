import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import type { ChatEntry } from "@/entities/chat"
import { ChatAnswer } from "@/features/map-chat/chat-answer"
import { LocaleProvider } from "@/shared/i18n"

vi.mock("@/features/map-chat/calculation/chat-calculation-run", () => ({
  ChatCalculationRun: ({ onSettled }: { onSettled: () => void }) => (
    <button type="button" onClick={onSettled}>
      finish-calculation
    </button>
  ),
}))
vi.mock("@/features/map-chat/analysis/chat-analysis-card", () => ({
  ChatAnalysisCard: ({
    analysis,
    onSettled,
  }: {
    analysis: { id: string }
    onSettled: () => void
  }) => (
    <button type="button" onClick={onSettled}>
      {analysis.id}
    </button>
  ),
}))
vi.mock("@/features/map-chat/calculation/chat-result-map", () => ({
  ChatResultMap: () => <div>result-map</div>,
}))

const base: ChatEntry = {
  id: "answer",
  role: "assistant",
  content: "first paragraph",
  complete: false,
  steps: [],
  tables: [],
  charts: [],
  mapCommands: [],
}

describe("chat output sequence", () => {
  it("keeps agent text intact and appends followups one at a time after the stream", () => {
    const message = {
      ...base,
      scenarios: [{ job_ids: ["job"] }],
      analyses: [{ id: "analysis-one" }, { id: "analysis-two" }],
    } as unknown as ChatEntry
    const draw = (complete: boolean) => (
      <LocaleProvider>
        <ChatAnswer message={{ ...message, complete }} onMapCommand={vi.fn()} />
      </LocaleProvider>
    )
    const view = render(draw(false))
    expect(screen.getByText(base.content)).toBeTruthy()
    expect(screen.queryByText("finish-calculation")).toBeNull()
    expect(screen.queryByText("analysis-one")).toBeNull()
    view.rerender(draw(true))
    expect(screen.getByText("finish-calculation")).toBeTruthy()
    expect(screen.queryByText("analysis-one")).toBeNull()
    fireEvent.click(screen.getByText("finish-calculation"))
    expect(screen.getByText("analysis-one")).toBeTruthy()
    expect(screen.queryByText("analysis-two")).toBeNull()
    fireEvent.click(screen.getByText("analysis-one"))
    expect(screen.getByText("analysis-two")).toBeTruthy()
    view.unmount()
  })
})
