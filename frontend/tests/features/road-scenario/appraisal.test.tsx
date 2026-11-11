import { fireEvent, render, screen } from "@testing-library/react"
import { useState } from "react"
import { describe, expect, it } from "vitest"
import { AppraisalNumber } from "@/features/road-scenario/appraisal/appraisal-number"
import {
  emptyPassenger,
  emptyProject,
  projectReady,
} from "@/features/road-scenario/appraisal/appraisal-state"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/appraisal.json"

function NumberEditor() {
  const [value, setValue] = useState(Number.NaN)
  return (
    <LocaleProvider>
      <AppraisalNumber label={ru.discount} value={value} onChange={setValue} />
    </LocaleProvider>
  )
}

describe("project appraisal inputs", () => {
  it("keeps decimal entry editable and accepts a comma separator", () => {
    render(<NumberEditor />)
    const input = screen.getByRole("textbox", { name: ru.discount }) as HTMLInputElement
    fireEvent.change(input, { target: { value: "1" } })
    fireEvent.change(input, { target: { value: "1," } })
    expect(input.value).toBe("1,")
    fireEvent.change(input, { target: { value: "1,5" } })
    expect(input.value).toBe("1.5")
    fireEvent.change(input, { target: { value: "" } })
    expect(input.value).toBe("")
  })

  it("requires documented flows and costs, and rejects duplicate directions", () => {
    const project = emptyProject()
    expect(projectReady(project)).toBe(false)
    const passenger = {
      ...emptyPassenger(),
      origin_point_id: "origin",
      market_city: "market",
      trips_per_year: 100,
      rub_per_hour: 200,
      source: "Explicit assumption",
    }
    const valid = {
      ...project,
      passengers: [passenger],
      capital_cost_rub: 0,
      annual_operating_cost_rub: 0,
      cost_source: "No additional costs assumed",
    }
    expect(projectReady(valid)).toBe(true)
    expect(projectReady({ ...valid, passengers: [passenger, passenger] })).toBe(false)
    expect(projectReady({ ...valid, discount_rate: -0.1 })).toBe(false)
  })
})
