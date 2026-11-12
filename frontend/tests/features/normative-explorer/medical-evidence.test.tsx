import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { expect, it } from "vitest"
import { NormativePointEvidence } from "@/features/normative-explorer/evidence/normative-point-evidence"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

it("shows the selected medical threshold and separate catchment and adjustment sources", () => {
  render(
    <MemoryRouter>
      <LocaleProvider>
        <NormativePointEvidence
          point={{
            id: "o",
            name: "Origin",
            population: 100,
            latitude: 55,
            longitude: 65,
            facility_id: "clinic",
            minutes: 46,
            excess_minutes: 1,
            state: "exceeded",
            threshold_minutes: 45,
            qualification_source_url: "https://example.org/evidence",
            qualification_observed_at: "2026-11-10",
            catchment_source_url: "https://example.org/catchment",
            threshold_source_url: "https://example.org/adjustment",
          }}
        />
      </LocaleProvider>
    </MemoryRouter>,
  )
  expect(screen.getByText(ru.selectedThresholdMinutes.replace("{{value}}", "45"))).toBeDefined()
  expect(screen.getByRole("link", { name: ru.catchmentSource }).getAttribute("href")).toBe(
    "https://example.org/catchment",
  )
  expect(screen.getByRole("link", { name: ru.thresholdSource }).getAttribute("href")).toBe(
    "https://example.org/adjustment",
  )
})
