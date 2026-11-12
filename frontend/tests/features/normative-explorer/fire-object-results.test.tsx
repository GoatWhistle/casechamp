import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { expect, it } from "vitest"
import type { Assessment } from "@/entities/normative"
import { NormativePanelResult } from "@/features/normative-explorer/normative-panel-result"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

const coverage = {
  population: 0,
  within: 0,
  exceeded: 0,
  unreachable: 0,
  unknown: 0,
  unknown_population_points: 1,
  not_regulated_population: 0,
  not_applicable_population: 0,
  not_regulated_points: 0,
  not_applicable_points: 0,
  excluded_unknown_population_points: 0,
  lower_percent: null,
  upper_percent: null,
}
const point = {
  id: "site-42",
  name: "Independent destination",
  population: null,
  latitude: 55,
  longitude: 65,
  facility_id: null,
  minutes: 14.5,
  excess_minutes: null,
  state: "unknown" as const,
  origin_source_url: "https://example.org/object-source",
  origin_observed_at: "2026-11-12",
  origin_reference_status: "verified_object",
}
const data: Assessment = {
  model_revision: "normative-v8",
  origin_basis: "fire_objects",
  criterion: {
    id: "N03",
    service: "fire",
    act: "123",
    clause: "76",
    source_url: "https://example.org/act",
    edition_date: "2026-11-12",
    threshold: 20,
    unit: "minutes",
    mode: "fire",
    territory: "Region",
    legal_status: "placement_requirement",
    verification_status: "currentness_unconfirmed",
  },
  facilities: [],
  graph_fingerprint: "a".repeat(64),
  graph_revision: "graph",
  region: "Region",
  closed_way_ids: [42],
  coverage_loss_pp: null,
  run_id: "test-object-run",
  baseline_rows: [{ ...point, minutes: 4.5 }],
  rows: [point],
  baseline: coverage,
  scenario: coverage,
}

it("labels the saved object basis and unknown object population", async () => {
  render(
    <LocaleProvider>
      <NormativePanelResult result={data} selectedPoint={null} />
    </LocaleProvider>,
  )
  expect(
    screen.getByText(ru.savedOriginBasis.replace("{{basis}}", ru.originBases.fire_objects)),
  ).toBeDefined()
  expect(screen.getByText(ru.objectPopulationUnknown)).toBeDefined()
  expect(screen.queryByText(ru.populationKnown)).toBeNull()
  await userEvent.click(screen.getByRole("button", { name: ru.tableOpen }))
  const table = screen.getByRole("table", { name: ru.objectResults })
  expect(within(table).getByRole("columnheader", { name: ru.destinationObject })).toBeDefined()
  expect(within(table).getByText("14,5")).toBeDefined()
})

it("uses baseline rows for the baseline point and table and keeps object evidence separate", async () => {
  render(
    <MemoryRouter>
      <LocaleProvider>
        <NormativePanelResult result={data} selectedPoint="site-42" routeStage="baseline" />
      </LocaleProvider>
    </MemoryRouter>,
  )
  await userEvent.click(screen.getByRole("button", { name: ru.tableOpen }))
  const table = screen.getByRole("table", { name: ru.objectResults })
  expect(within(table).getByText("4,5")).toBeDefined()
  expect(within(table).queryByText("14,5")).toBeNull()
  await userEvent.click(screen.getByRole("button", { name: ru.objectOriginSource }))
  expect(screen.getByText(ru.objectReferenceVerified)).toBeDefined()
  expect(screen.getByRole("link", { name: ru.openObjectSource }).getAttribute("href")).toBe(
    point.origin_source_url,
  )
  expect(screen.getAllByText(ru.states.unknown)).toHaveLength(2)
  expect(screen.queryByText(ru.states.within)).toBeNull()
})
