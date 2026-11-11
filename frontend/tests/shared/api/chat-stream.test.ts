import { afterEach, describe, expect, it, vi } from "vitest"
import { type ChatStreamEvent, streamChat } from "@/shared/api/chat-stream"
import chatCopy from "@/shared/i18n/locales/ru/chat.json"

const post = vi.hoisted(() => vi.fn())
vi.mock("@/shared/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/shared/api/client")>()
  return { ...original, api: { POST: post } }
})

function responseStream(text: string) {
  const bytes = new TextEncoder().encode(text)
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (let i = 0; i < bytes.length; i += 3) controller.enqueue(bytes.slice(i, i + 3))
      controller.close()
    },
  })
}

function mockResponse(text: string) {
  post.mockResolvedValue({
    data: responseStream(text),
    response: new Response(null, { status: 200 }),
  })
}

afterEach(() => vi.restoreAllMocks())

describe("chat stream", () => {
  it("decodes split Cyrillic bytes and multiple events", async () => {
    mockResponse(
      [
        { type: "delta", text: chatCopy.title, code: "" },
        { type: "delta", text: chatCopy.example, code: "" },
        { type: "done", text: "", code: "" },
      ]
        .map((event) => JSON.stringify(event))
        .join("\n"),
    )
    const events: ChatStreamEvent[] = []
    await streamChat({ prompt: "Hello" }, new AbortController().signal, (event) =>
      events.push(event),
    )
    expect(
      events
        .filter((event) => event.type === "delta")
        .map((event) => event.text)
        .join(""),
    ).toBe(chatCopy.title + chatCopy.example)
    expect(events.at(-1)?.type).toBe("done")
  })

  it("rejects premature EOF instead of showing a completed answer", async () => {
    mockResponse(JSON.stringify({ type: "delta", text: "Partial", code: "" }))
    await expect(
      streamChat({ prompt: "Hello" }, new AbortController().signal, () => undefined),
    ).rejects.toMatchObject({ code: "chat_stream_error" })
  })

  it("preserves safe server error codes", async () => {
    mockResponse(JSON.stringify({ type: "error", text: "", code: "chat_auth_required" }))
    await expect(
      streamChat({ prompt: "Hello" }, new AbortController().signal, () => undefined),
    ).rejects.toMatchObject({ code: "chat_auth_required" })
  })

  it.each([
    [429, "<html>Too Many Requests</html>", "chat_limit"],
    [502, "<html>Bad Gateway</html>", "chat_connection_error"],
    [503, { code: "server_unavailable" }, "chat_connection_error"],
    [504, "", "chat_connection_error"],
    [403, { code: "chat_local_only" }, "chat_local_only"],
  ])(
    "maps an HTTP %i response without NDJSON to a known chat code",
    async (status, error, code) => {
      post.mockResolvedValue({ error, response: new Response(null, { status }) })
      await expect(
        streamChat({ prompt: "Hello" }, new AbortController().signal, () => undefined),
      ).rejects.toMatchObject({ code })
    },
  )
})

it("accepts local artifacts and upstream scenarios in the same stream", async () => {
  const artifacts = [
    {
      type: "stress_test",
      stress_test: { id: "saved", version: "v", way_ids: [1], status: "completed", regions: [] },
    },
    { type: "scenario", scenario: { kind: "closure", job_ids: ["saved"] } },
    {
      type: "map",
      map: {
        action: "focus_settlement",
        region_ids: ["18000000"],
        settlement: {
          id: "town",
          name: "Town",
          region_id: "18000000",
          longitude: 44,
          latitude: 48,
        },
      },
    },
    {
      type: "table",
      table: {
        id: "pairs",
        title: "connectivity",
        columns: [{ key: "score", format: "number" }],
        rows: [{ score: 0 }],
        total: 1,
        source: "model:graph",
        truncated: false,
      },
    },
    { type: "done" },
  ].map((event) => ({ text: "", code: "", ...event }))
  mockResponse(artifacts.map((event) => JSON.stringify(event)).join("\n"))
  const events: ChatStreamEvent[] = []
  await streamChat({ prompt: "Review" }, new AbortController().signal, (event) =>
    events.push(event),
  )
  expect(events.map((event) => event.type)).toEqual(artifacts.map((event) => event.type))
})

it("sends calculation interpretation to the dedicated review endpoint", async () => {
  mockResponse(JSON.stringify({ type: "done", text: "", code: "" }))
  await streamChat(
    { prompt: "Review", calculation_review: { scenario_ids: ["saved"], stress_ids: [] } },
    new AbortController().signal,
    () => undefined,
  )
  expect(post.mock.calls.at(-1)?.[0]).toBe("/api/v1/chat/calculation-review")
})
