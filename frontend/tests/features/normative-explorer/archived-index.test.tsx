import { render, screen } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import type { IndexMapRegion } from "@/entities/normative"
import { RegionalIndexCard } from "@/features/normative-explorer/regional-inventory/regional-index-entry"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

const detail = vi.hoisted(() => vi.fn())
const archived: IndexMapRegion = {
  region_id: "26000000",
  region_name: "Region",
  value_min: 12,
  value_max: 15,
  weighting: "population",
  status: "scenario_ready",
  run_id: "archived",
  measured_at: "2026-11-01T00:00:00Z",
  threshold_min: 10,
  threshold_max: 20,
  unit: "minutes",
  reference_points: 100,
  measured_points: 90,
  legal_compliance_confirmed: false,
  data_source: "archived_aggregate",
  detail_available: false,
  source_report: "saved-report.json",
  source_report_sha256: "a".repeat(64),
  source_checked_at: "2026-11-12T00:00:00Z",
}
vi.mock("@/entities/normative", async (original) => ({
  ...(await original<typeof import("@/entities/normative")>()),
  useRegionalIndexMap: () => ({ data: [archived], isPending: false, isError: false }),
  useRegionalIndex: detail,
}))

it("shows the archived aggregate without requesting unavailable detailed results", () => {
  render(
    <LocaleProvider>
      <RegionalIndexCard regionId="26000000" criterionId="N01" stage="scenario" />
    </LocaleProvider>,
  )
  expect(screen.getByText(ru.archive.label)).toBeDefined()
  expect(screen.getByText(ru.archive.note)).toBeDefined()
  expect(detail).not.toHaveBeenCalled()
})
