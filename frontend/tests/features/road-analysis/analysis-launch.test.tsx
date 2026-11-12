import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { AnalysisPanel } from "@/features/road-analysis/analysis-panel"
import { LocaleProvider } from "@/shared/i18n"
import analysisRu from "@/shared/i18n/locales/ru/analysis.json"

const start = vi.hoisted(() => vi.fn())
vi.mock("@/entities/road-analysis", () => ({
  useRoadAnalysis: () => ({
    job: undefined,
    detail: { data: undefined },
    recent: [],
    start: { mutate: start, isPending: false },
    busy: false,
    error: false,
  }),
}))

vi.mock("@/features/road-analysis/analysis-results", () => ({
  AnalysisResults: () => null,
}))

describe("road search launch", () => {
  it("routes improvements into the traffic development conversation", () => {
    const onDevelop = vi.fn()
    render(
      <LocaleProvider>
        <AnalysisPanel
          regionId={null}
          mode="improvement"
          onOverlay={vi.fn()}
          onBack={vi.fn()}
          onDevelop={onDevelop}
        />
      </LocaleProvider>,
    )
    fireEvent.click(screen.getByRole("button", { name: analysisRu.start }))
    expect(onDevelop).toHaveBeenCalledOnce()
    expect(start).not.toHaveBeenCalled()
  })
})
