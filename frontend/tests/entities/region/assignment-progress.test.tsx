import { fireEvent, render, screen } from "@testing-library/react"
import { expect, it } from "vitest"
import { AssignmentProgress } from "@/entities/region"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/traffic.json"

it("shows measured convergence in an accessible tooltip", async () => {
  render(
    <LocaleProvider>
      <AssignmentProgress value={{ iteration: 7, relative_gap: 0.0071635, tolerance: 0.001 }} />
    </LocaleProvider>,
  )
  expect(
    screen.getByText(ru.assignmentIteration.replace("{{iteration, number}}", "7"), {
      exact: false,
      selector: "p",
    }),
  ).toBeTruthy()
  fireEvent.focus(screen.getByRole("button", { name: ru.assignmentAccuracy }))
  const tooltip = await screen.findByRole("tooltip")
  expect(tooltip.textContent).toContain("0,716")
  expect(tooltip.textContent).toContain("0,1")
})

it("does not invent convergence for historical jobs", () => {
  const view = render(
    <LocaleProvider>
      <AssignmentProgress value={undefined} />
    </LocaleProvider>,
  )
  expect(view.container.textContent).toBe("")
})
