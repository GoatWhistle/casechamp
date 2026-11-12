import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { expect, it } from "vitest"
import { NormativePoint } from "@/features/normative-explorer/normative-point"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

it("labels encoded municipality evidence as conditional and links both reference and rule", () => {
  render(
    <MemoryRouter>
      <LocaleProvider>
        <NormativePoint
          walking={false}
          library
          point={{
            id: "37502000101",
            name: "Origin",
            latitude: 55,
            longitude: 65,
            population: 100,
            facility_id: "library",
            minutes: 30,
            excess_minutes: null,
            state: "unknown",
            qualification_source_url: "https://example.org/evidence",
            qualification_observed_at: "2026-11-10",
            threshold_minutes: 60,
            territory_type: "municipal_okrug",
            municipality_code: "37502000",
            territory_verification_status: "encoded_parent_2024_assignment_unconfirmed",
            territory_source_url: "https://example.org/reference",
            territory_structure_source_url: "https://example.org/structure",
          }}
        />
      </LocaleProvider>
    </MemoryRouter>,
  )
  expect(screen.getByRole("link", { name: ru.qualificationSource }).getAttribute("href")).toBe(
    "https://example.org/evidence",
  )
  expect(
    screen.getByText(new RegExp(ru.qualificationObserved.replace("{{date}}", ""))),
  ).toBeDefined()
  expect(screen.getByText(ru.encodedTerritoryCandidate)).toBeDefined()
  expect(screen.getByText(ru.municipalityCode.replace("{{code}}", "37502000"))).toBeDefined()
  expect(screen.getByText(ru.states.unknown)).toBeDefined()
  expect(screen.queryByText(ru.states.within)).toBeNull()
  expect(screen.getByRole("link", { name: ru.territorySource }).getAttribute("href")).toBe(
    "https://example.org/reference",
  )
  expect(screen.getByRole("link", { name: ru.territoryStructureSource }).getAttribute("href")).toBe(
    "https://example.org/structure",
  )
})
