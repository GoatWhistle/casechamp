import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import type { ComparisonData } from "@/entities/accessibility/accessibility.queries"
import { ComparisonTables } from "@/entities/accessibility/comparison/comparison-tables"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/accessibility.json"
import common from "@/shared/i18n/locales/ru/common.json"

const data: ComparisonData = {
  region_id: "18000000",
  source_current: false,
  run: {
    run_id: "saved-run",
    created_at: "2026-11-10",
    model_version: "hansen-planned-v1",
    source_model: "legacy",
    source_artifact: "snapshot",
    normalization: 100,
    normalization_kind: "legacy_multimodal_road",
    regions: 82,
    markets: 180,
    point_count: 155412,
    frequency_status: "incomplete",
    assumptions: [],
  },
  rows: [
    {
      season: "summer",
      half_life: 2,
      previous: 100,
      potential: 99.97,
      delta: -0.03,
      without_air: 99.97,
      without_rail: 99.97,
      without_water: 99.97,
      population: 1000000,
      population_coverage: 1,
      scheduled_index: null,
    },
    {
      season: "winter",
      half_life: 2,
      previous: 0,
      potential: 2500,
      delta: 2500,
      without_air: 0,
      without_rail: 2500,
      without_water: 2400,
      population: 1000000,
      population_coverage: 1,
      scheduled_index: 0,
    },
  ],
  frequencies: [{ season: "summer", mode: "air", source: "trunk", total: 15000, known: 0 }],
}

describe("accessibility comparison", () => {
  it("distinguishes unavailable schedules, zero scores and negative change", () => {
    const result = render(
      <LocaleProvider>
        <ComparisonTables data={data} />
      </LocaleProvider>,
    )
    expect(result.container.querySelectorAll("[data-no-value]")).toHaveLength(1)
    expect(screen.getByText("-0,03")).toBeDefined()
    expect(screen.getAllByText(ru.effects).length).toBeGreaterThan(0)
    expect(screen.getAllByRole("button", { name: common.ui.hint })).toHaveLength(3)
    expect(screen.getAllByRole("table")).toHaveLength(3)
  })
})
