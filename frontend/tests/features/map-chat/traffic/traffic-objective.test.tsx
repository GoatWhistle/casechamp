import { render, screen, within } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { TrafficIndex } from "@/features/map-chat/traffic/traffic-index"
import { type TrafficJob, usefulTrafficAlternatives } from "@/shared/api/traffic"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/traffic.json"

function objectiveJob(objective: "transit" | "congestion"): TrafficJob {
  const baseline = {
    vehicle_hours: 10,
    unserved_vehicles: 0,
    overloaded_edges: 0,
    relative_gap: 0,
    converged: true,
    mean_trip_minutes: 20,
  }
  return {
    id: "traffic-goal",
    status: "completed",
    stage: "completed",
    version: "v2",
    completed: 3,
    total: 3,
    scope: {
      places: [],
      region: "",
      bounds: [],
      demand_multiplier: 1,
      pair_flow: 1000,
      max_projects: 3,
      objective,
    },
    bounds: [],
    zones: [],
    roads: [],
    baseline,
    provenance: "{}",
    error: "",
    indices: [],
    alternatives: [0.05, 0.2, 0].map((gain, index) => ({
      id: String(index),
      kind: index === 1 ? "capacity" : "closure",
      way_ids: [index],
      length_km: 1,
      vehicle_hours_saved: null,
      overload_increase: index === 1 ? 2 : 0,
      housing_clearance: true,
      roads: [],
      road_names: [],
      indices: [],
      objective_before: 0.5,
      objective_after: 0.5 - gain,
      objective_gain: gain,
      objective_unit: objective === "transit" ? "hours" : "vehicle_hours",
      after: { ...baseline, mean_trip_minutes: 21 },
    })),
  }
}

describe("traffic objective comparison", () => {
  it.each(["transit", "congestion"] as const)(
    "ranks %s gains without requiring a regional index or mean-trip improvement",
    (objective) => {
      const job = objectiveJob(objective)
      expect(usefulTrafficAlternatives(job).map((row) => row.id)).toEqual(["0", "1"])
      render(
        <LocaleProvider>
          <TrafficIndex job={job} variant="1" />
        </LocaleProvider>,
      )
      const table = screen.getByRole("table")
      expect(within(table).getAllByRole("row")[1]?.textContent).toContain(ru.kind.capacity)
      expect(within(table).getAllByRole("columnheader")).toHaveLength(2)
      expect(
        screen.getByText(objective === "transit" ? ru.transitMinutes : ru.congestionMinutes),
      ).toBeTruthy()
      expect(within(table).getAllByRole("row")[1]?.textContent).toContain("30,0")
      expect(within(table).getAllByRole("row")[1]?.textContent).toContain("18,0")
      expect(screen.queryByText(ru.indexUnavailable)).toBeNull()
      expect(screen.getByText(ru.overloadIncrease.replace("{{count, number}}", "2"))).toBeTruthy()
    },
  )

  it("retains convergence and road-clearance requirements for a positive objective gain", () => {
    const job = objectiveJob("transit")
    job.alternatives = job.alternatives.map((row, index) => ({
      ...row,
      kind: "connection",
      housing_clearance: index === 0,
      after: { ...row.after, converged: index !== 0 },
    }))
    expect(usefulTrafficAlternatives(job)).toEqual([])
  })
})
