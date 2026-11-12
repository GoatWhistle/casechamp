import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { expect, it } from "vitest"
import type { Assessment, Criterion } from "@/entities/normative"
import { NormativeSource } from "@/features/normative-explorer/normative-source"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

const savedCriterion: Criterion = {
  id: "N05",
  service: "mfc",
  act: "178",
  clause: "5",
  threshold: 60,
  unit: "minutes",
  mode: "car",
  territory: "Region",
  legal_status: "placement_requirement",
  verification_status: "published_edition",
  edition_date: "2023-02-08",
  source_url: "https://example.org/saved-edition",
}
const coverage = {
  population: 100,
  within: 0,
  unknown: 100,
  exceeded: 0,
  unreachable: 0,
  unknown_population_points: 0,
  not_regulated_population: 0,
  not_applicable_population: 0,
  not_regulated_points: 0,
  not_applicable_points: 0,
  excluded_unknown_population_points: 0,
  lower_percent: 0,
  upper_percent: 100,
}
const saved: Assessment = {
  criterion: savedCriterion,
  facilities: [],
  graph_fingerprint: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  graph_revision: "saved-network",
  model_revision: "saved-model",
  region: "Region",
  baseline: coverage,
  scenario: coverage,
  baseline_rows: [],
  rows: [],
  closed_way_ids: [],
  coverage_loss_pp: null,
  run_id: "saved-run",
  saved_at: "2026-11-12T02:00:00Z",
  qualification_as_of: "2026-11-11T23:00:00Z",
}

it("shows the saved legal source and timestamp even when the catalog changes", async () => {
  const current = { ...savedCriterion, clause: "99", source_url: "https://example.org/new-edition" }
  render(
    <MemoryRouter>
      <LocaleProvider>
        <NormativeSource criterion={current} result={saved} />
      </LocaleProvider>
    </MemoryRouter>,
  )
  await userEvent.click(screen.getByRole("button", { name: ru.sourceOpen }))
  expect(screen.getByRole("link", { name: ru.source }).getAttribute("href")).toBe(
    savedCriterion.source_url,
  )
  expect(screen.getByText(ru.clause.replace("{{clause}}", "5"))).toBeDefined()
  expect(screen.queryByText(ru.clause.replace("{{clause}}", "99"))).toBeNull()
  expect(screen.getByText(new RegExp(ru.savedAt.replace("{{date}}", ""))).textContent).toContain(
    "2026",
  )
  expect(screen.getByText(new RegExp(ru.qualificationAsOf.replace("{{date}}", "")))).toBeDefined()
  await userEvent.click(screen.getByRole("button", { name: ru.runDetails }))
  expect(
    screen.getByText(new RegExp(ru.modelRevision.replace("{{version}}", ""))).textContent,
  ).toContain("saved-model")
})
