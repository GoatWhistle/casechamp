import { useGeoRegions } from "../region.queries"
import styles from "./mini-map.module.css"

export interface MiniMapProps {
  readonly selectedId: string
}

export function MiniMap({ selectedId }: MiniMapProps) {
  const { data } = useGeoRegions()
  if (!data) return null
  const selected = data.regions.find((region) => region.id === selectedId)
  return (
    <svg className={styles.map} viewBox={data.view_box} aria-hidden="true">
      {data.regions.map((region) =>
        region.id === selectedId ? null : (
          <path key={region.id} className={styles.region} d={region.path_low ?? region.path} />
        ),
      )}
      {selected ? (
        <path className={styles.selected} d={selected.path_low ?? selected.path} />
      ) : null}
    </svg>
  )
}
