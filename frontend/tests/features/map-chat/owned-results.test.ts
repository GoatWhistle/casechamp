import { expect, it } from "vitest"
import type { ChatEntry } from "@/entities/chat"
import { ownedResults } from "@/features/map-chat/calculation/owned-results"
import { applyChatEvent } from "@/features/map-chat/chat-events"
import type { StressJob } from "@/shared/api/road-stress"

const job = { id: "closure", status: "completed" } as StressJob
const first: ChatEntry = {
  id: "first",
  role: "assistant",
  content: "Original interpretation",
  complete: true,
  steps: [],
  tables: [],
  charts: [],
  mapCommands: [],
  stressTests: [job],
}

it("keeps results on the original turn and does not repeat them under a followup question", () => {
  const followup = { ...first, id: "followup", content: "Explanation of a number" }
  const messages = [first, followup]
  expect(ownedResults(messages, 0).stressTests).toHaveLength(1)
  expect(ownedResults(messages, 1).stressTests).toHaveLength(0)
  expect(ownedResults(messages, 1).content).toBe(followup.content)
  expect(followup.stressTests).toHaveLength(1)
})

it("does not schedule an automatic review when a tool reads a completed result", () => {
  const row = applyChatEvent(
    { ...first, stressTests: [] },
    { type: "stress_test", code: "", text: "", stress_test: job },
  )
  expect(row.reviewPending).toBe(false)
  const running = applyChatEvent(
    { ...first, stressTests: [] },
    { type: "stress_test", code: "", text: "", stress_test: { ...job, status: "running" } },
  )
  expect(running.reviewPending).toBe(true)
  expect(
    applyChatEvent(running, { type: "stress_test", code: "", text: "", stress_test: job })
      .reviewPending,
  ).toBe(true)
})

it("updates a stress result without moving it behind the next scenario", () => {
  const second = { ...job, id: "second" }
  const row = applyChatEvent(
    { ...first, stressTests: [job, second] },
    {
      type: "stress_test",
      code: "",
      text: "",
      stress_test: { ...job, stage: "completed" },
    },
  )
  expect(row.stressTests?.map((item) => item.id)).toEqual([job.id, second.id])
})
