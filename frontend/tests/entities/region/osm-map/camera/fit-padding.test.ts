import type { Map as LibreMap } from "maplibre-gl"
import { expect, it } from "vitest"
import { fitPadding } from "@/entities/region/osm-map/camera/fit-padding"

const mapOf = (clientWidth: number, clientHeight: number) =>
  ({ getContainer: () => ({ clientWidth, clientHeight }) }) as unknown as LibreMap

it("keeps desktop padding when the map has room for it", () => {
  expect(fitPadding(mapOf(1040, 900), { top: 96, right: 56, bottom: 144, left: 56 })).toEqual({
    top: 96,
    right: 56,
    bottom: 144,
    left: 56,
  })
})

it("shrinks padding proportionally so it never takes more than half of a phone map", () => {
  const padding = fitPadding(mapOf(390, 370), { top: 100, right: 100, bottom: 100, left: 460 })
  expect(padding.left + padding.right).toBeCloseTo(195)
  expect(padding.left / padding.right).toBeCloseTo(4.6)
  expect(padding.top + padding.bottom).toBeCloseTo(185)
})

it("expands a uniform number into all four sides", () => {
  expect(fitPadding(mapOf(800, 600), 72)).toEqual({ top: 72, right: 72, bottom: 72, left: 72 })
})
