import type { Map as LibreMap } from "maplibre-gl"

export interface FitPadding {
  readonly top: number
  readonly right: number
  readonly bottom: number
  readonly left: number
}

const MAX_SHARE = 0.5

export function fitPadding(map: LibreMap, padding: number | FitPadding): FitPadding {
  const { clientWidth: width, clientHeight: height } = map.getContainer()
  const box =
    typeof padding === "number"
      ? { top: padding, right: padding, bottom: padding, left: padding }
      : padding
  const across = Math.min(1, (width * MAX_SHARE) / Math.max(1, box.left + box.right))
  const down = Math.min(1, (height * MAX_SHARE) / Math.max(1, box.top + box.bottom))
  return {
    top: box.top * down,
    right: box.right * across,
    bottom: box.bottom * down,
    left: box.left * across,
  }
}
