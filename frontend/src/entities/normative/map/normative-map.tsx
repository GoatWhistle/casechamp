import { useMemo } from "react"
import type { components } from "@/shared/api"
import styles from "./normative-map.module.css"

type Row = components["schemas"]["AccessResponse"]
type Facility = components["schemas"]["FacilityResponse"]

interface NormativeMapProps {
  readonly rows: readonly Row[]
  readonly facilities: readonly Facility[]
  readonly label: string
  readonly stateLabel: (state: Row["state"]) => string
}

export function NormativeMap({ rows, facilities, label, stateLabel }: NormativeMapProps) {
  const projection = useMemo(() => {
    const points = [...rows, ...facilities].filter(
      (point) => point.latitude !== null && point.longitude !== null,
    )
    const xs = points.map((point) => (point.longitude ?? 0) * Math.cos((Math.PI * 56) / 180))
    const ys = points.map((point) => -(point.latitude ?? 0))
    const west = Math.min(...xs),
      east = Math.max(...xs)
    const north = Math.min(...ys),
      south = Math.max(...ys)
    const scale = Math.min(960 / Math.max(east - west, 0.01), 460 / Math.max(south - north, 0.01))
    return (latitude: number, longitude: number) => ({
      x: 20 + (longitude * Math.cos((Math.PI * 56) / 180) - west) * scale,
      y: 20 + (-latitude - north) * scale,
    })
  }, [rows, facilities])
  return (
    <svg viewBox="0 0 1000 500" role="img" aria-label={label} className={styles.map}>
      <title>{label}</title>
      {rows.map((point) =>
        point.latitude === null || point.longitude === null ? null : (
          <circle
            key={point.id}
            cx={projection(point.latitude, point.longitude).x}
            cy={projection(point.latitude, point.longitude).y}
            r={point.state === "within" ? 3 : 2}
            className={styles.point}
            data-state={point.state}
          >
            <title>{`${point.name}: ${stateLabel(point.state)}`}</title>
          </circle>
        ),
      )}
      {facilities.map((point) =>
        point.latitude === null || point.longitude === null ? null : (
          <rect
            key={point.id}
            x={projection(point.latitude, point.longitude).x - 4}
            y={projection(point.latitude, point.longitude).y - 4}
            width={8}
            height={8}
            className={styles.facility}
          >
            <title>{point.name}</title>
          </rect>
        ),
      )}
    </svg>
  )
}
