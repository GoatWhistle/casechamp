import { describe, expect, it } from "vitest"
import { municipalAccessLayer } from "@/entities/region"
import { isChatMapCommand } from "@/shared/api/chat-map"
import type { components } from "@/shared/api/schema.gen"

const row = {
  id: "point",
  name: "Town",
  population: 10,
  latitude: 44,
  longitude: 42,
  facility_id: null,
  minutes: 70,
  excess_minutes: null,
  state: "unknown" as const,
  uncertainty: [],
}
const data: components["schemas"]["MunicipalAccessResponse"] = {
  region_id: "07000000",
  municipality_id: "district",
  criterion_id: "N01",
  source_sha256: "sha",
  run_id: "run",
  measured_at: "today",
  unit: "minutes",
  mode: "car",
  threshold: 60,
  reference_points: 2,
  measured_points: 1,
  unreachable_points: 1,
  unresolved_points: 0,
  deficit_points: 2,
  p90: 70,
  worst_decile_mean: 70,
  total: 2,
  offset: 0,
  limit: 100,
  legal_compliance_confirmed: false,
  percentile_basis: "finite_reference_points_nearest_rank",
  points: [
    { row, facility: null, deficit: true },
    {
      row: { ...row, id: "isolated", state: "unreachable", minutes: null },
      facility: null,
      deficit: true,
    },
  ],
}

it("colors measured deficits red without mutating saved qualification and preserves no-route state", () => {
  const layer = municipalAccessLayer(data, () => {})
  expect(layer?.rows.map((item) => item.state)).toEqual(["exceeded", "unreachable"])
  expect(data.points[0]?.row.state).toBe("unknown")
  expect(layer?.unit).toBe("minutes")
})

describe("municipal map command", () => {
  const command = {
    action: "focus",
    region_ids: ["07000000"],
    municipal_access: {
      region_id: "07000000",
      municipality_id: "district",
      criterion_id: "N01",
      threshold: 60,
    },
  }
  it("accepts a matching region and finite threshold", () => {
    expect(isChatMapCommand(command)).toBe(true)
  })
  it("rejects mismatched regions and invalid thresholds", () => {
    expect(
      isChatMapCommand({
        ...command,
        municipal_access: { ...command.municipal_access, region_id: "03000000" },
      }),
    ).toBe(false)
    expect(
      isChatMapCommand({
        ...command,
        municipal_access: { ...command.municipal_access, threshold: -1 },
      }),
    ).toBe(false)
  })
})
