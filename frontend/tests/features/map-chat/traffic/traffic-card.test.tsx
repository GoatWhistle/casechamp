import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { TrafficCard } from "@/features/map-chat/traffic/traffic-card"
import type { TrafficJob } from "@/shared/api/traffic"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/traffic.json"

const read = vi.hoisted(() => vi.fn())
vi.mock("@/shared/api/traffic", async (load) => ({
  ...(await load<typeof import("@/shared/api/traffic")>()),
  trafficJob: read,
}))
const metrics = {
  vehicle_hours: 100,
  mean_trip_minutes: 16.4,
  unserved_vehicles: 0,
  overloaded_edges: 1,
  relative_gap: 0,
  converged: true,
}
const job: TrafficJob = {
  id: "traffic-card",
  status: "completed",
  stage: "completed",
  version: "v3",
  completed: 3,
  total: 3,
  scope: {
    objective: "connectivity",
    places: [],
    region: "",
    bounds: [],
    demand_multiplier: 1,
    pair_flow: 1000,
    max_projects: 3,
  },
  bounds: [41, 43, 43, 45],
  zones: [],
  roads: [],
  baseline: metrics,
  provenance: "{}",
  error: "",
  indices: [
    { region: "Region", value: 99.15, population: 1000, settlements: 2, normalization: 100 },
  ],
  alternatives: [
    {
      id: "0",
      kind: "capacity",
      way_ids: [1],
      length_km: 1,
      overload_increase: 0,
      objective_unit: "",
      vehicle_hours_saved: 1,
      after: { ...metrics, mean_trip_minutes: 16.2 },
      roads: [],
      road_names: ["Road"],
      indices: [
        {
          region: "Region",
          before: 99.15,
          after: 99.15,
          delta: 0,
          relative_percent: 0,
          population: 1000,
        },
      ],
    },
  ],
}
function show(value: TrafficJob) {
  read.mockResolvedValue(value)
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <LocaleProvider>
        <TrafficCard initial={value} autoReview={false} onCommentary={() => undefined} />
      </LocaleProvider>
    </QueryClientProvider>,
  )
}
beforeEach(() => read.mockReset())
describe("complete road proposals", () => {
  it("keeps partial indices and alternatives out of the reply while work is running", () => {
    const result = show({ ...job, status: "running", stage: "index_comparing" })
    expect(screen.getByText(ru.verifying)).toBeTruthy()
    expect(screen.queryByRole("table")).toBeNull()
    expect(result.container.textContent).not.toContain("99,15")
  })
  it.each([
    ["loading", ru.preparing],
    ["candidates", ru.generating],
    ["comparing", ru.verifying],
  ])("names the %s phase without a single-minute completion promise", (stage, label) => {
    const result = show({ ...job, status: "running", stage })
    expect(screen.getByText(label)).toBeTruthy()
    expect(screen.queryByRole("table")).toBeNull()
    expect(result.container.textContent).not.toMatch(/60|120/)
  })
  it("shows local minutes beside the regional index without a wall of metadata", async () => {
    const result = show(job)
    expect(await screen.findByRole("table")).toBeTruthy()
    expect(screen.getByText("16,4")).toBeTruthy()
    expect(screen.getByText("16,2")).toBeTruthy()
    expect(screen.getByText(ru.unchanged)).toBeTruthy()
    expect(result.container.textContent).not.toContain("0,0000")
  })
})
