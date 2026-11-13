import { fireEvent, render, screen } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import { MunicipalSegmentActions } from "@/features/map-explorer/municipalities/municipal-segment-actions"
import type { TrafficRoad } from "@/shared/api/traffic"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/map.json"

const road: TrafficRoad = {
  way_id: 10,
  edge_index: 4,
  reverse_edge_index: 9,
  coordinates: [
    [42, 44],
    [42.01, 44.01],
  ],
  flow_before: 100,
  flow_after: 100,
  ratio_before: 0.2,
  ratio_after: 0.2,
  project: false,
  new_link: false,
}

it("closes one selected direction or both directions of the local segment", () => {
  const submit = vi.fn()
  render(
    <LocaleProvider>
      <MunicipalSegmentActions road={road} pending={false} onSubmit={submit} />
    </LocaleProvider>,
  )
  fireEvent.click(
    screen.getAllByRole("button", { name: ru.municipalTraffic.closeLane })[0] as HTMLElement,
  )
  expect(submit).toHaveBeenLastCalledWith("lane_closure", [4])
  fireEvent.click(screen.getByRole("button", { name: ru.municipalTraffic.reverseDirection }))
  fireEvent.click(
    screen.getAllByRole("button", { name: ru.municipalTraffic.closeLane })[0] as HTMLElement,
  )
  expect(submit).toHaveBeenLastCalledWith("lane_closure", [9])
  fireEvent.click(screen.getByRole("button", { name: ru.municipalTraffic.closeSegment }))
  expect(submit).toHaveBeenLastCalledWith("closure", [4, 9])
})
