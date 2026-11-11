import { render } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"
import { createChatSession } from "@/entities/chat/chat-session"
import { readChatArchive, writeChatArchive } from "@/entities/chat/session-storage"
import { ChatArtifacts } from "@/features/map-chat/chat-artifacts"
import { historyOf } from "@/features/map-chat/chat-history"
import { isChatTable, type ChatTable as Table } from "@/shared/api/chat-artifacts"
import { LocaleProvider } from "@/shared/i18n"

const table: Table = {
  id: "pairs",
  caption: "",
  title: "connectivity",
  columns: [
    { key: "origin", format: "text" },
    { key: "destination", format: "text" },
    { key: "hours_after", format: "number" },
    { key: "status_after", format: "text" },
    { key: "score_after", format: "number" },
  ],
  rows: [
    {
      id: "ab",
      origin: "A",
      destination: "B",
      hours_after: null,
      status_after: "unreachable",
      score_after: 0,
    },
    {
      id: "ac",
      origin: "A",
      destination: "C",
      hours_after: null,
      status_after: "unbound",
      score_after: null,
    },
  ],
  total: 2,
  truncated: false,
  source: "model:selected-settlements-road-v1:test",
}

afterEach(() => localStorage.clear())

describe("settlement connectivity tables", () => {
  it("does not append generated connectivity prose to the agent answer", () => {
    const summary: Table = { ...table, id: "summary", title: "connectivity_summary" }
    const view = render(
      <LocaleProvider>
        <ChatArtifacts
          tables={[summary, table, { ...table, id: "ranking", title: "sensitivity" }]}
          charts={[]}
        />
      </LocaleProvider>,
    )
    expect(view.container.querySelectorAll("table")).toHaveLength(1)
    view.unmount()
  })

  it("restores both table types from the existing chat archive", () => {
    const summary: Table = { ...table, id: "summary", title: "connectivity_summary" }
    expect(isChatTable(table)).toBe(true)
    expect(isChatTable(summary)).toBe(true)
    const session = createChatSession()
    session.messages.push({
      id: "answer",
      role: "assistant",
      content: "",
      complete: true,
      steps: [],
      tables: [summary, table],
      charts: [],
      mapCommands: [],
    })
    writeChatArchive({ sessions: [session], activeId: session.id }, new Map())
    const restored = readChatArchive()
    expect(restored.issue).toBe(false)
    expect(restored.sessions[0]?.messages[0]?.tables).toEqual([summary, table])
  })
  it("passes the saved calculation ID to the next turn even when prose omits it", () => {
    const summary: Table = {
      ...table,
      title: "connectivity_summary",
      rows: [
        {
          id: "connectivity-123",
          calculation_id: "connectivity-123",
          assumed_utilization: 0.5,
          duration_hours: 1,
        },
      ],
    }
    const history = historyOf([
      {
        id: "answer",
        role: "assistant",
        content: "",
        complete: true,
        steps: [],
        tables: [summary],
        charts: [],
        mapCommands: [],
      },
    ])
    expect(history).toHaveLength(1)
    expect(history[0]?.content).toContain('"calculation_id":"connectivity-123"')
  })
})
