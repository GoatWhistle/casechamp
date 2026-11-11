import { useCallback } from "react"
import { useSearchParams } from "react-router"

const VIEWS = [
  "home",
  "roads",
  "links",
  "connection",
  "result",
  "criticality",
  "improvement",
] as const

export type ScenarioView = (typeof VIEWS)[number]

const PARAM = "analysis_mode"

const isView = (value: string): value is ScenarioView =>
  (VIEWS as readonly string[]).includes(value)

export function scenarioViewOf(params: URLSearchParams): ScenarioView {
  const raw = params.get(PARAM)
  if (raw !== null && isView(raw)) return raw
  return raw === null && params.has("analysis") ? "criticality" : "home"
}

export function useScenarioView() {
  const [params, setParams] = useSearchParams()
  const view = scenarioViewOf(params)
  const setView = useCallback(
    (next: ScenarioView) =>
      setParams(
        (current) => {
          const updated = new URLSearchParams(current)
          updated.delete("analysis")
          if (next === "home") updated.delete(PARAM)
          else updated.set(PARAM, next)
          return updated
        },
        { replace: true },
      ),
    [setParams],
  )
  return { view, setView } as const
}
