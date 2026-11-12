import { fireEvent, render, renderHook, screen, within } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { TrafficIndex } from "@/features/map-chat/traffic/traffic-index"
import type { TrafficJob } from "@/shared/api/traffic"
import { useTrafficView } from "@/shared/hooks/use-traffic-view"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/traffic.json"

const job: TrafficJob = {
  id: "traffic-index",
  status: "completed",
  stage: "completed",
  version: "v2",
  completed: 2,
  total: 2,
  scope: {
    objective: "connectivity",
    places: [],
    region: "",
    bounds: [],
    demand_multiplier: 1,
    pair_flow: 1000,
    max_projects: 3,
  },
  bounds: [],
  zones: [],
  roads: [],
  baseline: {
    vehicle_hours: 100,
    unserved_vehicles: 0,
    overloaded_edges: 1,
    relative_gap: 0,
    converged: true,
    mean_trip_minutes: 20,
  },
  provenance: "{}",
  error: "",
  indices: [
    { region: "Region", value: 42.5, population: 1000, settlements: 2, normalization: 100 },
  ],
  alternatives: ["capacity", "connection"].map((kind, i) => ({
    id: String(i),
    kind: kind as "capacity" | "connection",
    way_ids: [1],
    length_km: 1,
    overload_increase: 0,
    objective_unit: "",
    vehicle_hours_saved: 999,
    housing_clearance: true,
    after: {
      vehicle_hours: 50,
      unserved_vehicles: 0,
      overloaded_edges: 1,
      relative_gap: 0,
      converged: true,
    },
    roads: [],
    road_names: ["Road"],
    indices: [
      {
        region: "Region",
        before: 42.5,
        after: 43.5 + i,
        delta: 1 + i,
        relative_percent: 2,
        population: 1000,
      },
    ],
  })),
}

describe("traffic index result", () => {
  it("leads with the calibrated index and ranks actual proposal effects", () => {
    render(
      <LocaleProvider>
        <TrafficIndex job={job} variant="1" />
      </LocaleProvider>,
    )
    expect(screen.getByText(/42,50/)).toBeTruthy()
    const table = screen.getByRole("table")
    expect(within(table).getAllByRole("row")[1]?.textContent).toContain(ru.kind.connection)
    expect(within(table).getAllByRole("columnheader")).toHaveLength(3)
    expect(screen.queryByText("999")).toBeNull()
    const selected = renderHook(() => useTrafficView())
    fireEvent.click(within(table).getByRole("button", { name: new RegExp(ru.kind.capacity) }))
    expect(selected.result.current.variant).toBe("0")
    expect(selected.result.current.job?.id).toBe(job.id)
  })
  it("keeps old traffic runs honest instead of substituting hours for an index", () => {
    render(
      <LocaleProvider>
        <TrafficIndex job={{ ...job, indices: [] }} variant="baseline" />
      </LocaleProvider>,
    )
    expect(screen.getByText(ru.indexUnavailable)).toBeTruthy()
    expect(screen.queryByRole("table")).toBeNull()
  })
  it("shows a local benefit with regional loss without a contradictory plus sign", () => {
    const proposal = job.alternatives[0]
    if (!proposal) throw new Error("Fixture proposal missing")
    const result = render(
      <LocaleProvider>
        <TrafficIndex
          variant="0"
          job={{
            ...job,
            alternatives: [
              {
                ...proposal,
                after: { ...proposal.after, mean_trip_minutes: 18 },
                indices: [
                  {
                    region: "Region",
                    before: 42.5,
                    after: 42.497,
                    delta: -0.003,
                    relative_percent: -0.01,
                    population: 1000,
                  },
                ],
              },
            ],
          }}
        />
      </LocaleProvider>,
    )
    expect(screen.getByText(ru.indexLoss.replace("{{value}}", "-0,0030"))).toBeTruthy()
    expect(result.container.textContent).not.toContain("+-")
  })
  it("does not recommend an unverified assignment even if local trip time looks better", () => {
    render(
      <LocaleProvider>
        <TrafficIndex
          variant="0"
          job={{
            ...job,
            alternatives: job.alternatives.map((proposal) => ({
              ...proposal,
              after: { ...proposal.after, converged: false, mean_trip_minutes: 1 },
              overload_increase: 0,
              vehicle_hours_saved: null,
            })),
          }}
        />
      </LocaleProvider>,
    )
    expect(screen.queryByRole("table")).toBeNull()
    expect(screen.getByText(ru.noImprovements)).toBeTruthy()
  })
  it("retains index gains from newly connected trips and names increased congestion", () => {
    const proposal = job.alternatives[0]
    if (!proposal) throw new Error("Fixture proposal missing")
    render(
      <LocaleProvider>
        <TrafficIndex
          variant="0"
          job={{
            ...job,
            alternatives: [
              {
                ...proposal,
                kind: "package",
                vehicle_hours_saved: null,
                overload_increase: 3,
                structures: [{ kind: "connection" }],
                housing_clearance: true,
              },
            ],
          }}
        />
      </LocaleProvider>,
    )
    expect(screen.getByRole("table")).toBeTruthy()
    expect(screen.getByText(ru.kind.package)).toBeTruthy()
    expect(screen.getByText(ru.overloadIncrease.replace("{{count, number}}", "3"))).toBeTruthy()
  })
  it("does not recommend a package with an unchecked new road", () => {
    const proposal = job.alternatives[0]
    if (!proposal) throw new Error("Fixture proposal missing")
    render(
      <LocaleProvider>
        <TrafficIndex
          variant="0"
          job={{
            ...job,
            alternatives: [
              {
                ...proposal,
                kind: "package",
                structures: [{ kind: "connection" }],
                housing_clearance: null,
              },
            ],
          }}
        />
      </LocaleProvider>,
    )
    expect(screen.queryByRole("table")).toBeNull()
  })
})
