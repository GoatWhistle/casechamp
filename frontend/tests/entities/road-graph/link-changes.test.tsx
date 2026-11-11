import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"
import { linkChangeText } from "@/entities/road-graph"
import { RoadJobSpec } from "@/features/road-scenario/road-job-spec"
import type { LinkChange, RoadJob } from "@/shared/api/road-graph"
import { i18n, LocaleProvider } from "@/shared/i18n"
import graph from "@/shared/i18n/locales/ru/graph.json"

const get = vi.hoisted(() => vi.fn())
vi.mock("@/shared/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/shared/api/client")>()
  return { ...original, api: { GET: get } }
})

const text = (change: LinkChange, names?: ReadonlyMap<string, string>) => {
  const value = linkChangeText(change, names)
  return i18n.t(value.key, value.values)
}

const ferry: LinkChange = {
  action: "remove",
  network: "local",
  mode: "ferry",
  source: "98614486101",
  target: "98626101001",
}

const HOURS = "{{hours, number(maximumFractionDigits: 1)}}"
const fill = (template: string, values: Record<string, string>) =>
  Object.entries(values).reduce(
    (result, [key, value]) => result.replace(key === "hours" ? HOURS : `{{${key}}}`, value),
    template,
  )

afterEach(() => get.mockReset())

describe("link change copy", () => {
  it("describes closures, additions and removals in Russian", () => {
    expect(
      text({ action: "remove", network: "intercity", mode: "air", source: "Surgut", target: "*" }),
    ).toBe(fill(graph.links.removeAll.air, { source: "Surgut" }))
    expect(
      text({
        action: "add",
        network: "intercity",
        mode: "rail",
        source: "Moscow",
        target: "Tver",
        hours: 1,
      }),
    ).toBe(fill(graph.links.add.rail, { source: "Moscow", target: "Tver", hours: "1" }))
    expect(
      text(
        ferry,
        new Map([
          ["98614486101", "Khoro"],
          ["98626101001", "Nyurba"],
        ]),
      ),
    ).toBe(fill(graph.links.remove.ferry, { source: "Khoro", target: "Nyurba" }))
    expect(text({ ...ferry, mode: "ice_crossing", action: "add", hours: 2.25 })).toBe(
      fill(graph.links.add.ice_crossing, {
        source: "98614486101",
        target: "98626101001",
        hours: "2,3",
      }),
    )
  })

  it("renders a links-only job without a road count and resolves names of both settlements", async () => {
    get.mockResolvedValue({
      data: [
        { point_id: "98614486101", name: "Khoro", region: "Sakha" },
        { point_id: "98626101001", name: "Nyurba", region: "Sakha" },
      ],
      response: new Response(null, { status: 200 }),
    })
    const job = {
      id: "job",
      region_id: "98000000",
      region: "Sakha",
      scenario: "summer",
      changes: [],
      links: [ferry],
      status: "completed",
      completed: 1,
      total: 1,
      version: "v",
    } as RoadJob
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={client}>
        <LocaleProvider>
          <RoadJobSpec job={job} />
        </LocaleProvider>
      </QueryClientProvider>,
    )
    expect(
      await screen.findByText(
        fill(graph.links.remove.ferry, { source: "Khoro", target: "Nyurba" }),
      ),
    ).toBeTruthy()
    expect(screen.getByText(graph.summary.links_one.replace("{{count, number}}", "1"))).toBeTruthy()
    expect(screen.getByText(graph.summer)).toBeTruthy()
    const roadCount = graph.summary.roads_one.split(",")[1]?.split("{{")[0]?.trim() ?? ""
    expect(document.body.textContent).not.toContain(roadCount)
    expect(get.mock.calls[0]?.[0]).toBe("/api/v1/road-graph/places")
    expect(get.mock.calls[0]?.[1]?.params.query).toEqual({
      ids: ["98614486101", "98626101001"],
    })
    client.clear()
  })
})
