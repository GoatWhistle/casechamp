import type { Locale } from "./locale"
import ruAccessibility from "./locales/ru/accessibility.json"
import ruAnalysis from "./locales/ru/analysis.json"
import ruAppraisal from "./locales/ru/appraisal.json"
import ruAtlas from "./locales/ru/atlas.json"
import ruCalendar from "./locales/ru/calendar.json"
import ruChat from "./locales/ru/chat.json"
import ruCommon from "./locales/ru/common.json"
import ruCompare from "./locales/ru/compare.json"
import ruData from "./locales/ru/data.json"
import ruErrors from "./locales/ru/errors.json"
import ruGraph from "./locales/ru/graph.json"
import ruHealth from "./locales/ru/health.json"
import ruLinks from "./locales/ru/links.json"
import ruMap from "./locales/ru/map.json"
import ruNav from "./locales/ru/nav.json"
import ruNormative from "./locales/ru/normative.json"
import ruProfile from "./locales/ru/profile.json"
import ruRegion from "./locales/ru/region.json"
import ruScenario from "./locales/ru/scenario.json"
import ruSeasons from "./locales/ru/seasons.json"
import ruSources from "./locales/ru/sources.json"
import ruStress from "./locales/ru/stress.json"
import ruTraffic from "./locales/ru/traffic.json"

export const NAMESPACES = [
  "common",
  "errors",
  "accessibility",
  "analysis",
  "appraisal",
  "atlas",
  "calendar",
  "chat",
  "compare",
  "data",
  "graph",
  "health",
  "links",
  "map",
  "nav",
  "normative",
  "profile",
  "region",
  "scenario",
  "seasons",
  "sources",
  "stress",
  "traffic",
] as const

export type Namespace = (typeof NAMESPACES)[number]

export const DEFAULT_NAMESPACE: Namespace = "common"

const ru = {
  common: ruCommon,
  errors: ruErrors,
  accessibility: ruAccessibility,
  analysis: ruAnalysis,
  appraisal: ruAppraisal,
  atlas: ruAtlas,
  calendar: ruCalendar,
  chat: ruChat,
  compare: ruCompare,
  data: ruData,
  graph: ruGraph,
  health: ruHealth,
  links: ruLinks,
  map: ruMap,
  nav: ruNav,
  normative: ruNormative,
  profile: ruProfile,
  region: ruRegion,
  scenario: ruScenario,
  seasons: ruSeasons,
  sources: ruSources,
  stress: ruStress,
  traffic: ruTraffic,
}

export type Dictionary = typeof ru

export const resources = { ru } satisfies Record<Locale, Record<Namespace, object>>
