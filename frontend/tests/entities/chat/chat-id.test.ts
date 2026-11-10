import { afterEach, describe, expect, it, vi } from "vitest"
import { createChatId } from "@/entities/chat/chat-id"

afterEach(() => vi.unstubAllGlobals())

describe("chat ids", () => {
  it("creates RFC 4122 ids where randomUUID is unavailable over plain HTTP", () => {
    const source = globalThis.crypto
    const getRandomValues = vi.fn((array: Uint8Array<ArrayBuffer>) => source.getRandomValues(array))
    vi.stubGlobal("crypto", { getRandomValues })
    const ids = new Set(Array.from({ length: 50 }, createChatId))
    expect(ids.size).toBe(50)
    expect(getRandomValues).toHaveBeenCalledTimes(50)
    for (const id of ids)
      expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/)
  })
})
