import { fireEvent, render, screen } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import { MunicipalityIndexCard } from "@/features/map-explorer/municipalities/municipality-index-card"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/map.json"
import { municipalIndices } from "./municipality-indices-fixture"

const query = vi.hoisted(() => vi.fn())
vi.mock("@/entities/region", async (original) => ({
  ...(await original<typeof import("@/entities/region")>()),
  useMunicipalityIndices: query,
  useMunicipalAccess: () => ({ isPending: true }),
  useMunicipalTraffic: () => ({ isPending: true }),
  useMunicipalScenario: () => ({ isPending: false, mutate: vi.fn() }),
}))

function card(id = "osm-relation-1") {
  return (
    <LocaleProvider>
      <MunicipalityIndexCard
        key={id}
        regionId="26000000"
        municipalityId={id}
        name="Municipality"
        season="summer"
        onClear={vi.fn()}
      />
    </LocaleProvider>
  )
}
const label = (key: string) => key.replace("{{name}}", "Municipality")

it("opens school and medical results immediately and restores a collapsed card without a new request", () => {
  query.mockReturnValue({ data: municipalIndices, isPending: false, isError: false })
  render(card())
  expect(query).toHaveBeenCalledWith("26000000", "osm-relation-1", "summer")
  expect(screen.getByText(ru.municipalCard.school)).toBeDefined()
  expect(screen.getByText(ru.municipalCard.medical)).toBeDefined()
  expect(
    screen.getByText(
      ru.municipalCard.thresholdPair.replace("{{min}}", "50 %").replace("{{max}}", "75 %"),
    ),
  ).toBeDefined()
  const calls = query.mock.calls.length
  fireEvent.click(screen.getByRole("button", { name: label(ru.municipalCard.collapse) }))
  const restore = screen.getByRole("button", { name: label(ru.municipalCard.restore) })
  expect(restore.getAttribute("aria-expanded")).toBe("false")
  fireEvent.click(restore)
  expect(
    screen
      .getByRole("button", { name: label(ru.municipalCard.collapse) })
      .getAttribute("aria-expanded"),
  ).toBe("true")
  expect(query).toHaveBeenCalledTimes(calls)
})

it("opens again for a different selected municipality", () => {
  query.mockReturnValue({ data: municipalIndices, isPending: false, isError: false })
  const { rerender } = render(card())
  fireEvent.click(screen.getByRole("button", { name: label(ru.municipalCard.collapse) }))
  rerender(card("osm-relation-2"))
  expect(
    screen
      .getByRole("button", { name: label(ru.municipalCard.collapse) })
      .getAttribute("aria-expanded"),
  ).toBe("true")
})

it("shows real pending service status without inventing a coverage value", () => {
  query.mockReturnValue({
    data: {
      ...municipalIndices,
      normative: municipalIndices.normative.map((row) => ({
        ...row,
        status: "pending",
        thresholds: [],
        values: [],
        value: null,
      })),
    },
    isPending: false,
    isError: false,
  })
  render(card())
  expect(screen.getAllByText(ru.municipalCard.pending)).toHaveLength(3)
  for (const explanation of screen.queryAllByText(ru.municipalCard.unavailable)) {
    expect(explanation.closest("[hidden]")).not.toBeNull()
  }
})

it("shows services and roads together without hidden metric sections", () => {
  query.mockReturnValue({ data: municipalIndices, isPending: false, isError: false })
  render(card())
  expect(screen.getByRole("region", { name: ru.municipalTraffic.title })).toBeDefined()
  expect(screen.getByRole("region", { name: ru.municipalCard.school })).toBeDefined()
  expect(screen.getByRole("region", { name: ru.municipalCard.medical })).toBeDefined()
  expect(screen.queryByRole("tab")).toBeNull()
})
