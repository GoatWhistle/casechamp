import { act, renderHook } from "@testing-library/react"
import { afterEach, beforeEach, expect, it } from "vitest"
import { usePanelDock } from "@/features/map-explorer/panel-dock/use-panel-dock"
import { COMPACT_LAYOUT } from "@/shared/hooks"

function phone(matches: boolean) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: (query: string) => ({
      matches: matches && query === COMPACT_LAYOUT,
      media: query,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    }),
  })
}

beforeEach(() => {
  localStorage.clear()
  phone(true)
})

afterEach(() => {
  Reflect.deleteProperty(window, "matchMedia")
})

it("opens the phone sheet at half height and flips between half and full", () => {
  const { result } = renderHook(() => usePanelDock({ current: null }))
  expect(result.current.phase).toBe("open")
  expect(result.current.sheet).toBe("half")
  act(() => result.current.toggleSheet(true))
  expect(result.current.sheet).toBe("full")
  expect(result.current.covering).toBe(true)
  act(() => result.current.toggleSheet(true))
  expect(result.current.sheet).toBe("half")
  expect(result.current.covering).toBe(false)
})

it("lowers a full sheet to half height when the map has to be seen", async () => {
  const { result } = renderHook(() => usePanelDock({ current: null }))
  act(() => result.current.toggleSheet(true))
  await act(async () => result.current.reveal())
  expect(result.current.sheet).toBe("half")
})

it("never resizes or covers the map on desktop", async () => {
  phone(false)
  const { result } = renderHook(() => usePanelDock({ current: null }))
  act(() => result.current.toggleSheet(true))
  expect(result.current.covering).toBe(false)
  await act(async () => result.current.reveal())
  expect(result.current.sheet).toBe("half")
})

it("reopens a collapsed sheet at half height and remembers the collapse", () => {
  const first = renderHook(() => usePanelDock({ current: null }))
  act(() => first.result.current.toggleSheet(true))
  act(() => first.result.current.collapse(true))
  expect(first.result.current.phase).toBe("closed")
  expect(first.result.current.sheet).toBe("half")
  const second = renderHook(() => usePanelDock({ current: null }))
  expect(second.result.current.phase).toBe("closed")
})
