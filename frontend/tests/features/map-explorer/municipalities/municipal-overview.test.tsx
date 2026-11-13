import { fireEvent, render, screen } from "@testing-library/react"
import { beforeEach, expect, it, vi } from "vitest"
import { MunicipalOverview } from "@/features/map-explorer/municipalities/municipal-overview"
import { LocaleProvider } from "@/shared/i18n"

const mocks = vi.hoisted(() => ({ query: vi.fn(), show: vi.fn() }))
vi.mock("@/entities/region", () => ({ useMunicipalOverview: mocks.query }))
vi.mock("@/shared/hooks/use-municipal-access-view", () => ({ showMunicipalAccess: mocks.show }))

beforeEach(() => {
  vi.clearAllMocks()
})

it("opens the connectivity ranking immediately without metric choices", () => {
  mocks.query.mockReturnValue({
    isPending: false,
    isError: false,
    data: {
      region_connectivity: { value: 20 },
      items: [
        {
          municipality_id: "district",
          name: "District",
          reasons: ["confirmed_service_deficit"],
          connectivity: { value: 10, population_coverage: 1 },
          service: {
            status: "available",
            criterion_id: "N04",
            threshold: 500,
            confirmed_deficit_percent: 20,
            possible_deficit_percent: 90,
          },
        },
      ],
    },
  })
  const select = vi.fn()
  render(
    <LocaleProvider>
      <MunicipalOverview regionId="07000000" season="winter" onSelect={select} onClear={vi.fn()} />
    </LocaleProvider>,
  )
  expect(mocks.query).toHaveBeenCalledWith("07000000", "", "winter")
  expect(screen.queryByRole("combobox")).toBeNull()
  fireEvent.click(screen.getByRole("button", { name: "District" }))
  expect(select).toHaveBeenCalledWith("district")
  expect(mocks.show).not.toHaveBeenCalled()
})
