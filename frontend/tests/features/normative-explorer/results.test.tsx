import { render, screen, within } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import type { Assessment } from "@/entities/normative"
import { NormativeResults } from "@/features/normative-explorer/normative-results"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

const data: Assessment = {
  model_revision: "unversioned",
  criterion: {
    id: "N05",
    service: "mfc",
    act: "178",
    clause: "5",
    source_url: "https://example.org",
    edition_date: "2023-02-08",
    threshold: 60,
    unit: "minutes",
    mode: "car",
    territory: "Region",
    legal_status: "placement_requirement",
    verification_status: "published_edition",
  },
  facilities: [],
  graph_fingerprint: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  graph_revision: "source-version",
  region: "Region",
  closed_way_ids: [],
  coverage_loss_pp: null,
  run_id: "test-run",
  baseline_rows: [],
  baseline: {
    population: 100,
    within: 60,
    unknown: 30,
    exceeded: 10,
    unreachable: 0,
    unknown_population_points: 0,
    not_regulated_population: 0,
    not_applicable_population: 0,
    not_regulated_points: 0,
    not_applicable_points: 0,
    excluded_unknown_population_points: 0,
    lower_percent: 60,
    upper_percent: 90,
  },
  scenario: {
    population: 100,
    within: 60,
    unknown: 30,
    exceeded: 10,
    unreachable: 0,
    unknown_population_points: 0,
    not_regulated_population: 0,
    not_applicable_population: 0,
    not_regulated_points: 0,
    not_applicable_points: 0,
    excluded_unknown_population_points: 0,
    lower_percent: 60,
    upper_percent: 90,
  },
  rows: [
    {
      id: "unknown",
      name: "A settlement with a very long name repeated for a realistic edge case",
      population: 30,
      latitude: null,
      longitude: null,
      facility_id: null,
      minutes: null,
      excess_minutes: null,
      state: "unknown",
    },
  ],
}

describe("normative results", () => {
  it("keeps unknown travel time distinct from a zero and shows coverage bounds", () => {
    const view = render(
      <LocaleProvider>
        <NormativeResults result={data} />
      </LocaleProvider>,
    )
    expect(
      screen.getByText(ru.bounds.replace("{{lower}}", "60,0").replace("{{upper}}", "90,0")),
    ).toBeDefined()
    const table = screen.getByRole("table")
    expect(within(table).getByText(ru.states.unknown)).toBeDefined()
    expect(view.container.querySelectorAll("[data-no-value]")).toHaveLength(1)
    expect(screen.getByRole("img", { name: ru.mapTitle })).toBeDefined()
  })

  it("does not claim a percentage when the population denominator is incomplete", () => {
    render(
      <LocaleProvider>
        <NormativeResults
          result={{
            ...data,
            scenario: {
              ...data.scenario,
              unknown_population_points: 1,
              not_regulated_population: 0,
              not_applicable_population: 0,
              not_regulated_points: 0,
              not_applicable_points: 0,
              excluded_unknown_population_points: 0,
              lower_percent: null,
              upper_percent: null,
            },
          }}
        />
      </LocaleProvider>,
    )
    expect(screen.getByText(ru.missingPopulation)).toBeDefined()
  })
})
