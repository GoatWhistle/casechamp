import { describe, expect, it } from "vitest"
import { chatStatusKey } from "@/features/map-chat/chat-copy"
import { applyChatEvent, streamStatus } from "@/features/map-chat/chat-events"
import type { ChatEntry } from "@/features/map-chat/use-map-chat"

const row: ChatEntry = {
  id: "a",
  role: "assistant",
  content: "",
  complete: false,
  steps: [],
  tables: [],
  charts: [],
  mapCommands: [],
}

describe("chat queue status", () => {
  it("shows waiting in queue without recording it as an action", () => {
    const event = { type: "status" as const, code: "queued", text: "" }
    expect(streamStatus("connecting", event)).toBe("queued")
    expect(chatStatusKey("queued")).toBe("chat:status.queued")
    expect(applyChatEvent(row, event).steps).toEqual([])
  })
})
