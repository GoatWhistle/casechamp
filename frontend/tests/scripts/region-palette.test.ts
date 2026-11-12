import { expect, it } from "vitest"
import { parseHex, relativeLuminance } from "../../scripts/checks/color"
import { readTokenSources, themeColor } from "../../scripts/tokenSources"

it("uses one progressively darker region scale shared by the map and legend", () => {
  const sources = readTokenSources(process.cwd())
  const values = Array.from({ length: 7 }, (_, index) =>
    themeColor(sources, "light", `--data-seq-${index + 1}`),
  )
  const luminances = values.map((value) => {
    const color = parseHex(value ?? "")
    expect(color).not.toBeNull()
    return color ? relativeLuminance(color) : 0
  })
  for (let index = 1; index < luminances.length; index++)
    expect(luminances[index]).toBeLessThan(luminances[index - 1] ?? 0)
  expect(new Set(values).size).toBe(7)
  expect(themeColor(sources, "light", "--map-none")).not.toBe(values[0])
})
