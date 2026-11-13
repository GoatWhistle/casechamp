import { act, fireEvent, render, screen } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import { Tooltip } from "@/shared/ui/overlays/tooltip/tooltip"

it("dismisses the visible tooltip before Escape reaches its containing panel", () => {
  vi.useFakeTimers()
  const parent = vi.fn()
  const view = render(
    <section aria-label="Panel" onKeyDown={parent}>
      <Tooltip content="Explanation">
        <button type="button">Help</button>
      </Tooltip>
    </section>,
  )
  try {
    const trigger = screen.getByRole("button", { name: "Help" })
    fireEvent.focus(trigger)
    act(() => vi.advanceTimersByTime(1000))
    expect(screen.getByRole("tooltip")).toBeDefined()
    fireEvent.keyDown(trigger, { key: "Escape" })
    expect(parent).not.toHaveBeenCalled()
    fireEvent.keyDown(trigger, { key: "Escape" })
    expect(parent).toHaveBeenCalledOnce()
  } finally {
    view.unmount()
    vi.useRealTimers()
  }
})
