import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, within } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { isAnalysisCommentary } from "@/entities/chat/session-validation"
import { ChatResultEvidence } from "@/features/map-chat/calculation/chat-result-evidence"
import { ChatArtifacts } from "@/features/map-chat/chat-artifacts"
import { type ChatTable, isChatTable } from "@/shared/api/chat-artifacts"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/chat.json"

const table: ChatTable = {
  id: "comparison",
  title: "scenario_indices",
  caption: "M-10",
  columns: [
    { key: "name", format: "text" },
    { key: "before", format: "number" },
    { key: "after", format: "number" },
    { key: "delta", format: "number" },
  ],
  rows: [{ id: "53", name: "Novgorod region", before: 84.144, after: 54.96, delta: -29.184 }],
  total: 1,
  truncated: false,
  source: "model:closure:123",
}

describe("server comparison tables", () => {
  it("renders compact verified data without a chart or model-authored markdown", () => {
    const view = render(
      <LocaleProvider>
        <ChatArtifacts tables={[table]} charts={[]} />
      </LocaleProvider>,
    )
    const rendered = screen.getByRole("table")
    expect(within(rendered).getAllByRole("columnheader")).toHaveLength(4)
    expect(within(rendered).getByText(ru.columns.before)).toBeTruthy()
    expect(within(rendered).getByText("Novgorod region")).toBeTruthy()
    expect(within(rendered).getByText("55,0")).toBeTruthy()
    expect(view.container.textContent).not.toContain("comparable_connections")
    view.unmount()
  })

  it("restores tables inside commentary and rejects malformed saved cells", () => {
    expect(isChatTable(table)).toBe(true)
    const commentary = { revision: "v", text: "", complete: true, error: null, tables: [table] }
    expect(isAnalysisCommentary(JSON.parse(JSON.stringify(commentary)))).toBe(true)
    expect(isAnalysisCommentary({ ...commentary, tables: [{ ...table, caption: 12 }] })).toBe(false)
  })
})

it("replaces an archived Markdown comparison with saved server columns", () => {
  const client = new QueryClient()
  client.setQueryData(["chat-calculation-tables", ["a"], []], [table])
  const view = render(
    <QueryClientProvider client={client}>
      <LocaleProvider>
        <ChatResultEvidence
          scenarioIds={["a"]}
          stressIds={[]}
          finished
          review={{
            revision: "v",
            complete: true,
            error: null,
            text: "Obsolete table\n| Region | Route |\n| --- | --- |\n| A | obsolete-values |",
          }}
        />
      </LocaleProvider>
    </QueryClientProvider>,
  )
  expect(screen.getByRole("table")).toBeTruthy()
  expect(view.container.textContent).not.toContain("obsolete-values")
  view.unmount()
  client.clear()
})
