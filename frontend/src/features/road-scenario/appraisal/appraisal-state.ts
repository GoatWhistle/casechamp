import type { components } from "@/shared/api/schema.gen"

export type Project = components["schemas"]["ProjectAssumptions"]
export type Passenger = components["schemas"]["PassengerFlow"]
export type Freight = components["schemas"]["FreightFlow"]

export function emptyProject(): Project {
  return {
    passengers: [],
    freight: [],
    scenarios: [
      { name: "low", demand_factor: 0.5, value_factor: 0.8 },
      { name: "base", demand_factor: 1, value_factor: 1 },
      { name: "high", demand_factor: 1.5, value_factor: 1.2 },
    ],
    capital_cost_rub: Number.NaN,
    annual_operating_cost_rub: Number.NaN,
    horizon_years: 20,
    discount_rate: 0.05,
    price_year: new Date().getFullYear(),
    cost_source: "",
  }
}

export function emptyPassenger(): Passenger {
  return {
    origin_point_id: "",
    market_city: "",
    trips_per_year: Number.NaN,
    rub_per_hour: Number.NaN,
    source: "",
    basis: "assumed",
    origin_name: "",
  }
}

export function emptyFreight(): Freight {
  return {
    name: "",
    origin_point_id: "",
    market_city: "",
    trips_per_year: Number.NaN,
    before_hours: Number.NaN,
    after_hours: Number.NaN,
    before_km: Number.NaN,
    after_km: Number.NaN,
    rub_per_vehicle_hour: Number.NaN,
    rub_per_km: Number.NaN,
    source: "",
    basis: "assumed",
  }
}

const nonnegative = (value: number | null) => value !== null && Number.isFinite(value) && value >= 0

function freightReady(flow: Freight): boolean {
  const routed = !!(flow.origin_point_id || flow.market_city)
  if (routed && !(flow.origin_point_id?.trim() && flow.market_city?.trim())) return false
  const travel =
    routed ||
    [flow.before_hours, flow.after_hours, flow.before_km, flow.after_km].every(nonnegative)
  return (
    !!flow.name.trim() &&
    !!flow.source.trim() &&
    travel &&
    [flow.trips_per_year, flow.rub_per_vehicle_hour, flow.rub_per_km].every(nonnegative)
  )
}

export function projectReady(project: Project | null): boolean {
  if (project === null) return true
  const freight = project.freight ?? []
  const count = project.passengers.length + freight.length
  return (
    count > 0 &&
    count <= 1000 &&
    nonnegative(project.capital_cost_rub) &&
    nonnegative(project.annual_operating_cost_rub) &&
    Number.isInteger(project.horizon_years) &&
    project.horizon_years >= 1 &&
    project.horizon_years <= 100 &&
    Number.isInteger(project.price_year) &&
    project.price_year >= 2000 &&
    project.price_year <= 2100 &&
    nonnegative(project.discount_rate) &&
    project.discount_rate <= 1 &&
    !!project.cost_source.trim() &&
    project.scenarios.every(
      (s, i, all) =>
        nonnegative(s.demand_factor) &&
        s.demand_factor <= 100 &&
        nonnegative(s.value_factor) &&
        s.value_factor <= 100 &&
        (!i ||
          (s.demand_factor >= (all[i - 1]?.demand_factor ?? 0) &&
            s.value_factor >= (all[i - 1]?.value_factor ?? 0))),
    ) &&
    project.passengers.every(
      (p) =>
        p.origin_point_id &&
        p.market_city &&
        p.source.trim() &&
        nonnegative(p.trips_per_year) &&
        nonnegative(p.rub_per_hour),
    ) &&
    new Set(project.passengers.map((p) => `${p.origin_point_id}/${p.market_city}`)).size ===
      project.passengers.length &&
    freight.every(freightReady) &&
    new Set(freight.map((f) => f.name.trim())).size === freight.length
  )
}
