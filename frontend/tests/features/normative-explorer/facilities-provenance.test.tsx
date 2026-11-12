import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { expect, it } from "vitest"
import type { Facility } from "@/entities/normative"
import { NormativeFacilities } from "@/features/normative-explorer/normative-facilities"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

const facility: Facility = {
  id: "library-1",
  service: "library",
  name: "Library",
  address: "Address",
  source_url: "https://example.org/library",
  observed_at: "2026-11-12",
  published_on: "2019-08-06",
  latitude: null,
  longitude: null,
  coordinate_source: null,
  coordinate_status: "missing",
}

function tree(row: Facility) {
  return (
    <MemoryRouter>
      <LocaleProvider>
        <NormativeFacilities facilities={[row]} />
      </LocaleProvider>
    </MemoryRouter>
  )
}

it("separates the original publication date from reading date and omits missing dates", () => {
  const view = render(tree(facility))
  const publishedLabel = new RegExp(ru.facilityPublished.replace("{{date}}", ""))
  expect(screen.getByText(publishedLabel).textContent).toContain("2019")
  expect(screen.getByText(new RegExp(ru.observed.replace("{{date}}", ""))).textContent).toContain(
    "2026",
  )
  view.rerender(tree({ ...facility, published_on: null }))
  expect(screen.queryByText(publishedLabel)).toBeNull()
})

it("shows the frozen document hash only when the API supplied one", async () => {
  const hash = "ab".repeat(32)
  const view = render(tree({ ...facility, source_sha256: hash }))
  await userEvent.click(screen.getByRole("button", { name: ru.facilities }))
  await userEvent.click(screen.getByRole("button", { name: facility.name }))
  await userEvent.click(screen.getByRole("button", { name: ru.documentVersion }))
  expect(screen.getByText(ru.documentSha256.replace("{{hash}}", hash))).toBeDefined()
  view.rerender(tree({ ...facility, source_sha256: null }))
  expect(screen.queryByRole("button", { name: ru.documentVersion })).toBeNull()
})

it("keeps the coordinate snapshot separate from the address document", async () => {
  const addressHash = "ab".repeat(32)
  const coordinateHash = "cd".repeat(32)
  render(
    tree({
      ...facility,
      latitude: 55,
      longitude: 65,
      coordinate_status: "geocoded_building",
      coordinate_source: "https://www.openstreetmap.org/way/42",
      source_sha256: addressHash,
      coordinate_snapshot_sha256: coordinateHash,
      coordinate_snapshot_url: "https://example.org/source.osm.pbf",
    }),
  )
  await userEvent.click(screen.getByRole("button", { name: ru.facilities }))
  await userEvent.click(screen.getByRole("button", { name: facility.name }))
  await userEvent.click(screen.getByRole("button", { name: ru.documentVersion }))
  await userEvent.click(screen.getByRole("button", { name: ru.coordinateVersion }))
  expect(screen.getByText(ru.documentSha256.replace("{{hash}}", addressHash))).toBeDefined()
  expect(
    screen.getByText(ru.coordinateSnapshotSha256.replace("{{hash}}", coordinateHash)),
  ).toBeDefined()
  expect(screen.getByText(ru.coordinateSnapshotNote)).toBeDefined()
  expect(screen.getByRole("link", { name: ru.coordinateSnapshotSource }).getAttribute("href")).toBe(
    "https://example.org/source.osm.pbf",
  )
  expect(screen.getByRole("link", { name: ru.coordinateSource }).getAttribute("href")).toBe(
    "https://www.openstreetmap.org/way/42",
  )
})
