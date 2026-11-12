import { fireEvent, render, screen } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import type { useMunicipalities } from "@/entities/region"
import { MunicipalityControl } from "@/features/map-explorer/municipalities/municipality-control"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/map.json"

type Query = ReturnType<typeof useMunicipalities>

it("keeps the toolbar empty when no district geometry was returned", () => {
  const query = { isPending: false, isError: false, data: { features: [] } } as unknown as Query
  const { container } = render(
    <LocaleProvider>
      <MunicipalityControl query={query} selected={null} onSelect={vi.fn()} />
    </LocaleProvider>,
  )
  expect(container.textContent).toBe("")
})

it("keeps retry available after a failed district request", () => {
  const refetch = vi.fn()
  const query = { isPending: false, isError: true, refetch } as unknown as Query
  render(
    <LocaleProvider>
      <MunicipalityControl query={query} selected={null} onSelect={vi.fn()} />
    </LocaleProvider>,
  )
  fireEvent.click(screen.getByRole("button", { name: ru.municipalities.retry }))
  expect(refetch).toHaveBeenCalledOnce()
})
