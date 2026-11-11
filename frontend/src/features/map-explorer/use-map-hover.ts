import { useCallback, useRef, useState } from "react"
import { placeHoverCard } from "./hover-card"

export function useMapHover() {
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const currentId = useRef<string | null>(null)
  const cardRef = useRef<HTMLDivElement | null>(null)
  const point = useRef({ x: 0, y: 0 })
  const onHover = useCallback((id: string | null, x: number, y: number) => {
    point.current = { x, y }
    if (id !== currentId.current) {
      currentId.current = id
      setHoveredId(id)
    }
    if (id !== null && cardRef.current) placeHoverCard(cardRef.current, x, y)
  }, [])
  return { hoveredId, cardRef, point, onHover }
}
