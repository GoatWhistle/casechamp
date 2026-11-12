import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { expect, it } from "vitest"
import { NormativePoint } from "@/features/normative-explorer/normative-point"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

it("shows the call threshold and separate speed and method evidence without changing unknown state", () => {
  render(
    <MemoryRouter>
      <LocaleProvider>
        <NormativePoint
          fire
          walking={false}
          point={{
            id: "o",
            name: "Call",
            population: 100,
            latitude: 55,
            longitude: 65,
            facility_id: "depot",
            minutes: 12,
            excess_minutes: null,
            state: "unknown",
            threshold_minutes: 20,
            territory_source_url: "https://example.org/place",
            qualification_source_url: "https://example.org/evidence",
            travel_profile_source_url: "https://example.org/speed",
            measurement_method_source_url: "https://example.org/method",
          }}
        />
      </LocaleProvider>
    </MemoryRouter>,
  )
  expect(screen.getByText(ru.fireThresholdMinutes.replace("{{value}}", "20"))).toBeDefined()
  expect(screen.getByRole("link", { name: ru.travelProfileSource }).getAttribute("href")).toBe(
    "https://example.org/speed",
  )
  expect(screen.getByRole("link", { name: ru.measurementMethodSource }).getAttribute("href")).toBe(
    "https://example.org/method",
  )
  expect(screen.getByRole("link", { name: ru.fireSettlementSource }).getAttribute("href")).toBe(
    "https://example.org/place",
  )
  expect(screen.getByText(ru.states.unknown)).toBeDefined()
  expect(screen.queryByText(ru.states.within)).toBeNull()
})
