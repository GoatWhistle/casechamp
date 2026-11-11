import { act, renderHook } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { showStressView, updateStressGeometry, useStressView } from "@/shared/hooks/use-stress-view"

describe("stress map state", () => {
  it("keeps closure geometry when opening another result of the same job", () => {
    const { result } = renderHook(() => useStressView())
    act(() => {
      showStressView({ jobId: "a", impacts: [], route: null })
      updateStressGeometry("a", [
        [
          [30, 50],
          [31, 51],
        ],
      ])
      showStressView({ jobId: "a", impacts: [], route: null, regions: [] })
    })
    expect(result.current.closed).toEqual([
      [
        [30, 50],
        [31, 51],
      ],
    ])
    act(() => showStressView({ jobId: "b", impacts: [], route: null }))
    expect(result.current.closed).toBeUndefined()
  })
  it("ignores late geometry after changing the active chat", () => {
    const { result } = renderHook(() => useStressView())
    act(() => {
      showStressView({ jobId: null, impacts: [], route: null })
      updateStressGeometry("old", [
        [
          [30, 50],
          [31, 51],
        ],
      ])
    })
    expect(result.current.closed).toBeUndefined()
  })
})
