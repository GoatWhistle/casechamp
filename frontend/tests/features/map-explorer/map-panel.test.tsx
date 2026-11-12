import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { afterEach, describe, expect, it, vi } from "vitest"
import type { Overview, RegionSummary } from "@/entities/region"
import { MapPanel } from "@/features/map-explorer/summary/map-panel"
import { LocaleProvider } from "@/shared/i18n"
import map from "@/shared/i18n/locales/ru/map.json"

const get = vi.hoisted(() => vi.fn())
vi.mock("@/shared/api/client", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/shared/api/client")>()
  return { ...original, api: { GET: get } }
})

const region: RegionSummary = {
  id: "46000000",
  name: "Moscow Oblast",
  settlements: 10,
  population: 1000,
  links: 5,
  links_season: 5,
  companies: null,
  revenue_rub: null,
  hansen: 10,
  has_geometry: true,
}
const overview = {
  regions: 1,
  settlements: 10,
  population: 1000,
  links: 5,
  companies: null,
  revenue_rub: null,
  index: { status: "ready" },
} as unknown as Overview

const clients: QueryClient[] = []
afterEach(() => {
  clients.splice(0).forEach((client) => {
    client.clear()
  })
  get.mockReset()
})

function setup(selectedId: string) {
  get.mockResolvedValue({
    error: { code: "region_not_found" },
    response: new Response(null, { status: 404 }),
  })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  clients.push(client)
  render(
    <QueryClientProvider client={client}>
      <LocaleProvider>
        <MemoryRouter>
          <MapPanel
            overview={overview}
            regions={[region]}
            metric="hansen"
            season="summer"
            selectedId={selectedId}
            selectedName="Moscow"
            searchFor={(id) => `?region=${id}`}
            onClear={() => undefined}
          />
        </MemoryRouter>
      </LocaleProvider>
    </QueryClientProvider>,
  )
}

describe("map panel selection outside the model", () => {
  it("explains a federal city without requesting a model region that does not exist", async () => {
    setup("45000000")
    const note = map.selected.outsideModel_one
      .replace("{{name}}", "Moscow")
      .replace("{{count}}", "1")
    expect(await screen.findByText(note)).toBeTruthy()
    await new Promise((resolve) => setTimeout(resolve, 20))
    const requested = get.mock.calls.filter((call) => JSON.stringify(call).includes("45000000"))
    expect(requested).toEqual([])
  })
})
