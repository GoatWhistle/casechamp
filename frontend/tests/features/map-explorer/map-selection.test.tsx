import { act, renderHook } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import { useMapSelection } from "@/features/map-explorer/selection/use-map-selection"

it("preserves settlement focus and clears commands on manual normative region selection", () => {
  const select = vi.fn()
  const { result } = renderHook(() => useMapSelection([{ id: "26000000" }], select))
  act(() =>
    result.current.onMapCommand({
      action: "focus_settlement",
      region_ids: ["26000000"],
      settlement: { id: "1", name: "Place", region_id: "26000000", longitude: 42, latitude: 45 },
    }),
  )
  expect(select).toHaveBeenLastCalledWith("26000000")
  expect(result.current.mapCommand?.action).toBe("focus_settlement")
  act(() => result.current.selectRegion(null))
  expect(select).toHaveBeenLastCalledWith(null)
  expect(result.current.mapCommand).toBeNull()
})
