import { fireEvent, render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { afterEach, expect, it, vi } from "vitest"
import type { ChatEntry } from "@/entities/chat"
import { MapChat } from "@/features/map-chat/map-chat"
import { LocaleProvider } from "@/shared/i18n"
import copy from "@/shared/i18n/locales/ru/chat.json"

const chat = vi.hoisted(() => ({ messages: [] as ChatEntry[] }))
vi.mock("@/features/map-chat/use-map-chat", () => ({
  useMapChat: () => ({
    ...chat,
    sessions: [],
    status: "writing",
    draft: "",
    sessionId: "chat",
    busy: true,
  }),
}))
vi.mock("@/entities/region", () => ({ useRegion: () => ({}) }))
vi.mock("@/features/map-chat/chat-answer", () => ({ ChatAnswer: () => null }))
afterEach(() => vi.unstubAllGlobals())

it("preserves the reading position after a small upward scroll during streaming", () => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
    },
  )
  const message: ChatEntry = {
    id: "answer",
    role: "assistant",
    content: "answer",
    complete: false,
    steps: [],
    tables: [],
    charts: [],
    mapCommands: [],
  }
  chat.messages = [message]
  const draw = () => (
    <MemoryRouter>
      <LocaleProvider>
        <MapChat
          context={{ season: "summer", network_mode: "road", metric: "hansen" }}
          summary={null}
          onMapCommand={vi.fn()}
        />
      </LocaleProvider>
    </MemoryRouter>
  )
  const view = render(draw())
  const scroll = screen.getByRole("region", { name: copy.history })
  Object.defineProperties(scroll, {
    scrollHeight: { configurable: true, value: 1000 },
    clientHeight: { configurable: true, value: 400 },
  })
  scroll.scrollTop = 600
  fireEvent.scroll(scroll)
  fireEvent.wheel(scroll, { deltaY: -40 })
  scroll.scrollTop = 560
  fireEvent.scroll(scroll)
  chat.messages = [{ ...message, content: "answer continues" }]
  view.rerender(draw())
  expect(scroll.scrollTop).toBe(560)
  scroll.scrollTop = 600
  fireEvent.scroll(scroll)
  chat.messages = [{ ...message, content: "more" }]
  Object.defineProperty(scroll, "scrollHeight", { configurable: true, value: 1100 })
  view.rerender(draw())
  expect(scroll.scrollTop).toBe(1100)
  view.unmount()
})
