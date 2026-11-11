import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { expect, it, vi } from "vitest"
import { MapChat } from "@/features/map-chat/map-chat"
import { type ChatInput, type ChatStreamEvent, streamChat } from "@/shared/api/chat-stream"
import { LocaleProvider } from "@/shared/i18n"
import copy from "@/shared/i18n/locales/ru/chat.json"

vi.mock("@/shared/api/chat-stream", async (load) => ({
  ...(await load<typeof import("@/shared/api/chat-stream")>()),
  streamChat: vi.fn(),
}))

it("asks for sources after completion and displays the reply with the original answer context", async () => {
  localStorage.clear()
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe = vi.fn()
      disconnect = vi.fn()
      unobserve = vi.fn()
    },
  )
  const pending: {
    body: ChatInput
    emit: (event: ChatStreamEvent) => void
    finish: () => void
  }[] = []
  vi.mocked(streamChat).mockImplementation(
    (body, _signal, emit) => new Promise<void>((finish) => pending.push({ body, emit, finish })),
  )
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const view = render(
    <QueryClientProvider client={client}>
      <LocaleProvider>
        <MemoryRouter>
          <MapChat
            context={{ season: "summer", network_mode: "road", metric: "hansen" }}
            selection={null}
            regionCard={() => null}
            roads={[]}
            onClearRoads={vi.fn()}
            onMapCommand={vi.fn()}
          />
        </MemoryRouter>
      </LocaleProvider>
    </QueryClientProvider>,
  )
  try {
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Compare regions" } })
    fireEvent.click(screen.getByRole("button", { name: copy.send }))
    await waitFor(() => expect(pending).toHaveLength(1))
    expect(screen.queryByRole("button", { name: copy.showSources })).toBeNull()
    const answer = "The regions differ.\n\nSources: [Atlas](/api/v1/sources)"
    await act(async () => {
      pending[0]?.emit({ type: "status", text: "", code: "sources" })
      pending[0]?.emit({
        type: "table",
        text: "",
        code: "",
        table: {
          id: "regions",
          title: "regions",
          columns: [{ key: "name", format: "text" }],
          rows: [{ id: "17", name: "Vladimir" }],
          source: "/api/v1/regions",
          total: 1,
          truncated: false,
        },
      })
      pending[0]?.emit({ type: "delta", text: answer, code: "" })
      pending[0]?.emit({ type: "done", text: "", code: "" })
      pending[0]?.finish()
    })
    expect(screen.queryByRole("link", { name: "Atlas" })).toBeNull()
    expect(screen.queryByRole("link", { name: copy.tableSource })).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: copy.showSources }))
    await waitFor(() => expect(pending).toHaveLength(2))
    expect(pending[1]?.body.prompt).toBe(copy.showSources)
    expect(pending[1]?.body.history?.at(-1)?.content).toContain(answer)
    expect(pending[1]?.body.history?.at(-1)?.content).toContain('"source":"/api/v1/regions"')
    await act(async () => {
      pending[1]?.emit({ type: "delta", text: "Sources: [Atlas](/api/v1/sources)", code: "" })
      pending[1]?.emit({ type: "done", text: "", code: "" })
      pending[1]?.finish()
    })
    expect(screen.getByRole("link", { name: "Atlas" }).getAttribute("href")).toBe("/api/v1/sources")
    expect(screen.queryByRole("button", { name: copy.showSources })).toBeNull()
  } finally {
    view.unmount()
    client.clear()
    vi.mocked(streamChat).mockReset()
    vi.unstubAllGlobals()
    localStorage.clear()
  }
})
