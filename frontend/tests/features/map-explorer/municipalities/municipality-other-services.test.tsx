import { render, screen } from "@testing-library/react"
import { expect, it } from "vitest"
import { MunicipalityOtherServices } from "@/features/map-explorer/municipalities/municipality-other-services"
import { LocaleProvider } from "@/shared/i18n"
import data from "@/shared/i18n/locales/ru/data.json"
import ru from "@/shared/i18n/locales/ru/map.json"
import { service } from "./municipality-indices-fixture"

it("shows actual available secondary services with their existing criterion names", () => {
  render(
    <LocaleProvider>
      <MunicipalityOtherServices
        rows={[
          { ...service("N03", [10, 20], [25, 50]), mode: "emergency_response" },
          service("N05", [15], [80]),
          { ...service("N08", [20], [0]), status: "unavailable", values: [] },
        ]}
      />
    </LocaleProvider>,
  )
  expect(screen.getByText(data.metric.normative_N03)).toBeDefined()
  expect(screen.getByText(data.metric.normative_N05)).toBeDefined()
  const help = screen.getByRole("button", {
    name: ru.municipalCard.metricHelp.replace("{{name}}", data.metric.normative_N03),
  })
  const description = document.getElementById(help.getAttribute("aria-describedby") ?? "")
  expect(description?.textContent).toContain(ru.municipalCard.fireAssumption)
  expect(screen.queryByText(data.metric.normative_N08)).toBeNull()
})

it("adds no empty service rows when secondary measurements are unavailable", () => {
  const { container } = render(
    <LocaleProvider>
      <MunicipalityOtherServices
        rows={[{ ...service("N05", [15], [0]), status: "unavailable", values: [] }]}
      />
    </LocaleProvider>,
  )
  expect(container.textContent).toBe("")
})
