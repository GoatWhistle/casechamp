import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { expect, it, vi } from "vitest"
import { FireScenarioFields, useFireScenario } from "@/features/normative-explorer/fire-scenario"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

function Form({ count = 0, error = false, retry = () => {} }) {
  const state = useFireScenario(true)
  return (
    <LocaleProvider>
      <FireScenarioFields
        enabled
        state={state}
        objectCount={count}
        objectError={error}
        onRetryObjects={retry}
      />
      <output data-testid="parameters">{JSON.stringify(state.parameters)}</output>
    </LocaleProvider>
  )
}

async function selectObjects() {
  await userEvent.click(screen.getByRole("combobox", { name: ru.originBasisLabel }))
  await userEvent.click(screen.getByRole("option", { name: ru.originBases.fire_objects }))
}

it("keeps an empty object registry distinct from settlement references", async () => {
  render(<Form />)
  expect(screen.getByText(ru.settlementReferenceNote)).toBeDefined()
  await selectObjects()
  expect(screen.getByText(ru.fireObjectsEmpty)).toBeDefined()
  expect(screen.getByText(ru.fireObjectsEmptyHint)).toBeDefined()
  expect(screen.queryByText(ru.settlementReferenceNote)).toBeNull()
  await userEvent.type(screen.getByRole("textbox", { name: ru.fireSpeed }), "40")
  await userEvent.type(
    screen.getByRole("textbox", { name: ru.fireAssumption }),
    "Control assumption",
  )
  expect(JSON.parse(screen.getByTestId("parameters").textContent ?? "{}")).toEqual({
    origin_basis: "fire_objects",
    fire_profile: { speed_kmh: 40, assumption: "Control assumption" },
  })
})

it("reports loaded object count without substituting settlement count", async () => {
  render(<Form count={7} />)
  await selectObjects()
  expect(screen.getByText(ru.fireObjectCount.replace("{{value}}", "7"))).toBeDefined()
  expect(screen.queryByText(ru.fireObjectsEmpty)).toBeNull()
})

it("offers retry for a failed registry instead of calling it empty", async () => {
  const retry = vi.fn()
  render(<Form error retry={retry} />)
  await selectObjects()
  expect(screen.getByText(ru.fireObjectsError)).toBeDefined()
  expect(screen.queryByText(ru.fireObjectsEmpty)).toBeNull()
  const button = screen.getByRole("button", { name: /./ })
  await userEvent.click(button)
  expect(retry).toHaveBeenCalledOnce()
})
