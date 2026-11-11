import { useEffect } from "react"
import { useLocation } from "react-router"

function revealRequested(state: unknown): boolean {
  return typeof state === "object" && state !== null && "reveal" in state
}

export function useReveal(cardId: string, ready: boolean, regionId: string) {
  const location = useLocation()
  const reveal = revealRequested(location.state)
  useEffect(() => {
    if (!ready || !reveal || regionId === "") return
    const card = document.getElementById(cardId)
    if (!card) return
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    card.scrollIntoView({ block: "start", behavior: still ? "auto" : "smooth" })
    card.focus({ preventScroll: true })
  }, [cardId, ready, reveal, regionId])
}
