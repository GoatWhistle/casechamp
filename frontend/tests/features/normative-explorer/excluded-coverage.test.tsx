import { render, screen } from "@testing-library/react"
import { expect, it } from "vitest"
import type { Assessment } from "@/entities/normative"
import { NormativeCoverage } from "@/features/normative-explorer/normative-coverage"
import { NormativePopulation } from "@/features/normative-explorer/normative-population"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

const counts = {
  population: 0,
  within: 0,
  exceeded: 0,
  unreachable: 0,
  unknown: 0,
  unknown_population_points: 0,
  lower_percent: null,
  upper_percent: null,
  not_regulated_population: 0,
  not_applicable_population: 0,
  not_regulated_points: 1,
  not_applicable_points: 0,
  excluded_unknown_population_points: 1,
}
const data: Assessment = {
  criterion: {
    id: "N09",
    service: "stop",
    act: "178",
    clause: "22",
    source_url: "https://example.org/rule",
    edition_date: "2023-02-08",
    threshold: 500,
    unit: "metres",
    mode: "walk",
    territory: "Region",
    legal_status: "placement_requirement",
    verification_status: "verified",
  },
  facilities: [],
  graph_revision: "network",
  graph_fingerprint: "fingerprint",
  model_revision: "normative-v4",
  region: "Region",
  baseline: counts,
  scenario: counts,
  baseline_rows: [],
  closed_way_ids: [],
  coverage_loss_pp: null,
  run_id: "run",
  rows: [
    {
      id: "building",
      name: "Building",
      population: null,
      latitude: 55,
      longitude: 65,
      facility_id: null,
      minutes: null,
      excess_minutes: null,
      state: "not_regulated",
    },
  ],
}

it("does not show an unregulated population as zero access or unknown eligible residents", () => {
  render(
    <LocaleProvider>
      <NormativeCoverage result={data} />
      <NormativePopulation result={data} />
    </LocaleProvider>,
  )
  expect(screen.getByText(ru.numericCoverageUnavailable)).toBeDefined()
  expect(screen.getByText(ru.numericCoverageExplanation)).toBeDefined()
  expect(screen.getByText(ru.unregulatedPoints)).toBeDefined()
  expect(screen.getByText(ru.excludedDenominator)).toBeDefined()
  expect(screen.queryByText(ru.populationNotKnown)).toBeNull()
})
