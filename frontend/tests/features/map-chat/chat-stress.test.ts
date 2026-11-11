import { describe, expect, it } from "vitest"
import { type ChatEntry, createChatSession } from "@/entities/chat/chat-session"
import { isChatSession } from "@/entities/chat/session-validation"
import { updateChatRows } from "@/features/map-chat/chat-events"
import { historyContent } from "@/features/map-chat/chat-history"
import type { StressJob, StressRouteComparison } from "@/shared/api/road-stress"

const job: StressJob = {
  id: "saved-stress",
  version: "v",
  way_ids: [1],
  status: "completed",
  stage: "completed",
  completed: 180,
  total: 180,
  points: 2,
  unbound_points: 0,
  preexisting_isolated_points: 0,
  newly_isolated_points: 0,
  regions: [],
}
const point = {
  id: "a",
  name: "Origin",
  region: "Region",
  population: 10,
  node: 1,
  snap_km: 0,
  longitude: 30,
  latitude: 50,
}
const route: StressRouteComparison = {
  origin: point,
  destination: { ...point, id: "b" },
  before: {
    status: "reachable",
    hours: 1,
    km: 50,
    coordinates: [
      [30, 50],
      [31, 51],
    ],
  },
  after: { status: "unreachable", hours: null, km: null, coordinates: [] },
}
const row: ChatEntry = {
  id: "message",
  role: "assistant",
  content: "",
  complete: false,
  steps: [],
  tables: [],
  charts: [],
  mapCommands: [],
}

describe("stress artifacts in conversation history", () => {
  it("stores a live job and detour together and restores validated history", () => {
    let rows = updateChatRows([row], row.id, {
      type: "stress_test",
      text: "",
      code: "",
      stress_test: job,
      stress_route: route,
    })
    rows = updateChatRows(rows, row.id, { type: "done", text: "", code: "" })
    const saved = JSON.parse(JSON.stringify({ ...createChatSession(), messages: rows }))
    expect(isChatSession(saved)).toBe(true)
    expect(saved.messages[0].stressRoutes[job.id].after.status).toBe("unreachable")
    const restored = rows[0]
    if (!restored) throw new Error("Missing restored message")
    expect(historyContent(restored)).toContain(
      '"job_id":"saved-stress","origin":"a","destination":"b"',
    )
  })
})
