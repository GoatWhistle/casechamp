import { render, screen } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import type { ChatEntry } from "@/entities/chat"
import { CalculationProgress } from "@/features/map-chat/calculation/calculation-progress"
import type { StressJob } from "@/shared/api/road-stress"
import { LocaleProvider } from "@/shared/i18n"

vi.mock("@/features/map-chat/calculation/calculation-name", () => ({ CalculationName: () => null }))

vi.mock("@/features/map-chat/calculation/chat-result-map", () => ({ ChatResultMap: () => null }))

it("shows the actual stage percentage for parallel jobs and collapses completed stages", () => {
  const jobs = [
    { id: "one", stage: "routes", status: "running", completed: 116, total: 180 },
    { id: "two", stage: "completed", status: "completed", completed: 180, total: 180 },
  ] as StressJob[]
  const message: ChatEntry = {
    id: "message",
    role: "assistant",
    content: "",
    complete: true,
    tables: [],
    charts: [],
    mapCommands: [],
    steps: [],
  }
  const view = render(
    <LocaleProvider>
      <CalculationProgress jobs={jobs} message={message} progress={null} label="progress" />
    </LocaleProvider>,
  )
  expect(screen.getAllByRole("progressbar")).toHaveLength(1)
  expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe("64")
  expect(screen.getAllByRole("listitem")).toHaveLength(4)
  expect(view.container.querySelector('[aria-current="step"]')?.textContent).toBeTruthy()
  expect(screen.getByText("100%")).toBeTruthy()
  view.unmount()
})
