import type { components } from "./schema.gen"

export type ChatScenario = components["schemas"]["ScenarioCard"]
export type ChatScenarioKind = ChatScenario["kind"]

const KINDS: readonly string[] = ["closure", "roads", "connection", "links"]

export function isChatScenario(value: unknown): value is ChatScenario {
  if (typeof value !== "object" || value === null) return false
  if (!("kind" in value) || !("job_ids" in value)) return false
  return (
    typeof value.kind === "string" &&
    KINDS.includes(value.kind) &&
    Array.isArray(value.job_ids) &&
    value.job_ids.length > 0 &&
    value.job_ids.every((id: unknown) => typeof id === "string")
  )
}
