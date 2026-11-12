import type { components } from "@/shared/api"

type Response = components["schemas"]["MunicipalityIndicesResponse"]
type Normative = Response["normative"][number]

export function service(
  criterion_id: string,
  thresholds: number[],
  shares: number[],
  population = false,
): Normative {
  return {
    criterion_id,
    value: shares[0] ?? null,
    status: "available",
    reason: null,
    basis_kind: "scenario_reference",
    qualification: "physical_only",
    legal_compliance_confirmed: false,
    unit: criterion_id === "N04" ? "metres" : "minutes",
    mode: criterion_id === "N04" ? "walk" : "car",
    thresholds,
    values: thresholds.map((threshold, index) => ({
      threshold,
      reference_points: 100,
      measured_points: 100,
      within_points: shares[index] ?? 0,
      unresolved_points: 0,
      point_share_percent: shares[index] ?? null,
      population: population ? 1000 : null,
      within_population: population ? (shares[index] ?? 0) * 10 : null,
      population_share_percent: population ? (shares[index] ?? null) : null,
    })),
    mean_travel: 420,
    measured_points: 100,
    reference_points: 100,
    facilities: 4,
    model_revision: "model",
    definition_sha256: "definition",
    source_urls: [],
    origin_kind:
      criterion_id === "N04" ? "residential_reference_points" : "settlement_reference_points",
  }
}

const connectivity: Response["connectivity"] = {
  key: "hansen_idx",
  value: 110,
  status: "available",
  reason: null,
  unit: "index_points",
  population: 1000,
  measured_population: 900,
  settlements: 10,
  measured_settlements: 9,
  population_coverage: 0.9,
}

export const municipalIndices: Response = {
  region_id: "26000000",
  municipality_id: "osm-relation-1",
  name: "Municipality",
  season: "road",
  connectivity,
  region_connectivity: { ...connectivity, value: 120 },
  metrics: [],
  normative: [
    service("N04", [500, 800, 1000], [50, 60, 75]),
    service("N01", [60], [60], true),
    service("N02", [120], [90], true),
  ],
  method: "measured_points",
  model_version: "model",
  artifact_version: "artifact",
  source_table: "points",
  computed_at: "2026-11-13T00:00:00Z",
  boundary_source_url: "https://example.com",
  boundary_source_sha256: "boundary",
}
