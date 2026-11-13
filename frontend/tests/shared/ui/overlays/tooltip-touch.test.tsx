import { act, fireEvent, render, screen } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import { Tooltip } from "@/shared/ui/overlays/tooltip/tooltip"

function pointerDown(pointerType: string) {
  const event = new Event("pointerdown", { bubbles: true })
  Object.defineProperty(event, "pointerType", { value: pointerType })
  document.dispatchEvent(event)
}

it("does not open a tooltip when focus follows a touch, and opens it again after a key press", () => {
  vi.useFakeTimers()
  const view = render(
    <Tooltip content="Explanation">
      <button type="button">Help</button>
    </Tooltip>,
  )
  try {
    const trigger = screen.getByRole("button", { name: "Help" })
    pointerDown("touch")
    fireEvent.focus(trigger)
    act(() => vi.advanceTimersByTime(1000))
    expect(screen.queryByRole("tooltip")).toBeNull()
    fireEvent.blur(trigger)
    fireEvent.keyDown(document, { key: "Tab" })
    fireEvent.focus(trigger)
    act(() => vi.advanceTimersByTime(1000))
    expect(screen.getByRole("tooltip")).toBeDefined()
  } finally {
    view.unmount()
    vi.useRealTimers()
  }
})
