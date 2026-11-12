import { type KeyboardEvent, useEffect, useRef, type WheelEvent } from "react"
import type { ChatEntry } from "@/entities/chat"

export function useChatScroll(tail: ChatEntry | undefined) {
  const scroll = useRef<HTMLDivElement>(null)
  const follow = useRef(true)
  const previousTop = useRef(0)
  useEffect(() => {
    const node = scroll.current
    if (tail === undefined || !node) return
    const sync = () => {
      if (!follow.current) return
      node.scrollTop = node.scrollHeight
      previousTop.current = node.scrollTop
    }
    sync()
    const observer = new ResizeObserver(sync)
    for (const child of node.children) observer.observe(child)
    return () => observer.disconnect()
  }, [tail])

  const scrollProps = {
    onScroll: () => {
      const node = scroll.current
      if (!node) return
      if (node.scrollTop < previousTop.current) follow.current = false
      else if (node.scrollHeight - node.scrollTop - node.clientHeight <= 2) follow.current = true
      previousTop.current = node.scrollTop
    },
    onWheelCapture: (event: WheelEvent<HTMLDivElement>) => {
      if (event.deltaY < 0) follow.current = false
    },
    onPointerDownCapture: () => {
      follow.current = false
    },
    onKeyDownCapture: (event: KeyboardEvent<HTMLDivElement>) => {
      if (
        ["ArrowUp", "PageUp", "Home"].includes(event.key) ||
        (event.key === " " && event.shiftKey)
      )
        follow.current = false
    },
  }
  return { scroll, follow, scrollProps }
}
