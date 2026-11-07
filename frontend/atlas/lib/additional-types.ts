export type Sector = {
  region_id: string; sector: string; company_rows: number; revenue_rows: number;
  strict_rows: number; strict_revenue_rows: number; strict_revenue_rub: number | null;
};
export type RegionEconomy = {
  region_id: string; name: string; population: number; company_rows: number;
  revenue_rows: number; strict_rows: number; strict_revenue_rows: number;
  strict_revenue_rub: number | null; fns_matched_rows: number; strict_fns_rows: number;
  strict_fns_income_rub: number | null; sectors: Sector[];
  lights: {year: number; points: number; valid_points: number; mean_raw: number | null;
    median_raw: number | null; zero_points: number}[];
};
export type SettlementEconomy = {
  point_id: string; region_id: string; name: string; population: number; lat: number; lon: number;
  company_rows: number; revenue_rows: number; revenue_rub: number | null;
  market_weight_rub: number | null; fns_matched_rows: number; max_assignment_km: number | null;
  light_2023: number | null; light_2024: number | null;
};
export type RouteSeason = {
  route_id: string; region_id: string; route: string; district: string; season_end_year: number;
  opening_date: string; closure_date: string; report_date: string; road_km: string;
  elapsed_days: number | null; weight_limit_tonnes: number | null; restriction_start_date: string;
  status: string; source_url: string | null; source_file: string; pdf_page: number;
  stop_ids: string[]; unresolved_stops: string[];
};
export type SourceEntry = {id: string; title: string; table: string; period: string;
  url: string | null; note: string; rows: number};
export type AdditionalData = {
  schema_version: number; strict_filter: string; generated_at: string; financial_year: number; assignment_radius_km: number;
  regions: RegionEconomy[]; route_seasons: RouteSeason[]; sources: SourceEntry[];
  summary: {source_company_rows: number; atlas_company_rows: number; outside_atlas_rows: number;
    revenue_rows: number; strict_rows: number; strict_revenue_rows: number;
    fns_source_rows: number; fns_matched_rows: number; settlement_assigned_rows: number};
  context: Record<string, Record<string, string | null>[]>;
  economic_access: {status: string; rows: number};
  outside_atlas: {source_region: string; rows: number}[];
};
