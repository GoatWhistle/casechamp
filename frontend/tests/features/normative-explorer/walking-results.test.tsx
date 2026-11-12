import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it } from "vitest"
import type { Assessment } from "@/entities/normative"
import { NormativePanelResult } from "@/features/normative-explorer/normative-panel-result"
import { LocaleProvider } from "@/shared/i18n"
import common from "@/shared/i18n/locales/ru/common.json"
import ru from "@/shared/i18n/locales/ru/normative.json"

const coverage = {
  population: 0,
  within: 0,
  unknown: 0,
  exceeded: 0,
  unreachable: 0,
  unknown_population_points: 125,
  not_regulated_population: 0,
  not_applicable_population: 0,
  not_regulated_points: 0,
  not_applicable_points: 0,
  excluded_unknown_population_points: 0,
  lower_percent: null,
  upper_percent: null,
}
const data: Assessment = {
  model_revision: "unversioned",
  criterion: {
    id: "N04",
    service: "school",
    act: "19",
    clause: "13.1",
    source_url: "https://example.org",
    edition_date: "2026-06-02",
    threshold: 500,
    unit: "metres",
    mode: "walk",
    territory: "Region",
    legal_status: "placement_requirement",
    verification_status: "currentness_unconfirmed",
  },
  facilities: [],
  graph_fingerprint: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  graph_revision: "walking-test",
  region: "Region",
  closed_way_ids: [],
  coverage_loss_pp: null,
  run_id: "walking-run",
  baseline_rows: [],
  baseline: coverage,
  scenario: coverage,
  rows: Array.from({ length: 125 }, (_, index) => ({
    id: `building-${index}`,
    name: `Building ${index}`,
    population: null,
    latitude: 55,
    longitude: 65,
    facility_id: "school",
    minutes: null,
    excess_minutes: null,
    distance_metres: 1000 + index,
    state: "unknown",
    uncertainty: ["population_group_missing"],
  })),
}

describe("walking results", () => {
  it("shows metres and paginates references without inventing a population denominator", async () => {
    render(
      <LocaleProvider>
        <NormativePanelResult result={data} selectedPoint={null} />
      </LocaleProvider>,
    )
    expect(screen.getByText(ru.populationNotKnown)).toBeDefined()
    expect(screen.queryByText(ru.populationKnown)).toBeNull()
    await userEvent.click(screen.getByRole("button", { name: ru.tableOpen }))
    const table = screen.getByRole("table", { name: ru.residentialBuildings })
    expect(within(table).getByRole("columnheader", { name: ru.distanceMetres })).toBeDefined()
    expect(within(table).queryByRole("columnheader", { name: ru.minutes })).toBeNull()
    expect(within(table).getAllByRole("row")).toHaveLength(51)
    expect(within(table).getByText("Building 124")).toBeDefined()
    await userEvent.click(screen.getByRole("button", { name: common.ui.pagination.next }))
    expect(within(table).queryByText("Building 124")).toBeNull()
    expect(within(table).getByText("Building 74")).toBeDefined()
  })

  it("explains why a measured reference path does not prove normative access", async () => {
    render(
      <LocaleProvider>
        <NormativePanelResult result={data} selectedPoint="building-0" />
      </LocaleProvider>,
    )
    expect(screen.getAllByText(ru.states.unknown).length).toBeGreaterThan(0)
    await userEvent.click(screen.getByRole("button", { name: ru.unknownReasons }))
    expect(screen.getByText(ru.uncertainty.population_group_missing)).toBeDefined()
    expect(screen.queryByText(ru.states.within)).toBeNull()
  })

  it("finds an off-page reference by identifier without changing coverage", async () => {
    render(
      <LocaleProvider>
        <NormativePanelResult result={data} selectedPoint={null} />
      </LocaleProvider>,
    )
    await userEvent.click(screen.getByRole("button", { name: ru.tableOpen }))
    await userEvent.click(screen.getByRole("button", { name: common.ui.pagination.next }))
    await userEvent.type(screen.getByRole("textbox", { name: ru.pointSearch }), "BUILDING-124")
    const table = screen.getByRole("table", { name: ru.residentialBuildings })
    expect(within(table).getAllByRole("row")).toHaveLength(2)
    expect(within(table).getByText("Building 124")).toBeDefined()
    expect(screen.getByText(ru.populationNotKnown)).toBeDefined()
  })
})
