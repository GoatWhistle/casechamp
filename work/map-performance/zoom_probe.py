import asyncio
import json
import os
import statistics
import sys

from playwright.async_api import async_playwright

BASE = os.environ.get("PROBE_URL", "http://localhost:8080")
CHROME = os.path.expanduser("~/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome")
CPU = float(os.environ.get("PROBE_CPU", "4"))
DPR = float(os.environ.get("PROBE_DPR", "1"))
CATEGORIES = ["devtools.timeline", "disabled-by-default-devtools.timeline", "toplevel", "v8"]
CHILD = ["FunctionCall", "TimerFire", "FireAnimationFrame", "EventDispatch", "UpdateLayoutTree", "Layout",
         "PrePaint", "Paint", "Layerize", "HitTest", "MajorGC", "MinorGC", "V8.GC_SCAVENGER", "ParseHTML"]

INSTRUMENT = """() => {
  window.__frames = []; window.__long = []; window.__dswaps = 0; window.__attrs = {};
  let last = performance.now();
  const tick = (t) => { window.__frames.push(t - last); last = t; if (window.__rec) requestAnimationFrame(tick) };
  window.__rec = true; requestAnimationFrame(tick);
  window.__obs = new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__long.push(Math.round(e.duration))));
  window.__obs.observe({ type: 'longtask' });
  const surface = document.querySelector('[data-map-surface]');
  window.__mo = new MutationObserver((records) => {
    for (const r of records) {
      const key = r.target.tagName + '.' + r.attributeName;
      window.__attrs[key] = (window.__attrs[key] || 0) + 1;
    }
  });
  window.__mo.observe(surface, { attributes: true, subtree: true });
}"""
STOP = """() => { window.__rec = false; window.__obs.disconnect(); window.__mo.disconnect();
  const view = document.querySelector('[data-map-surface]').dataset.view;
  return { frames: window.__frames.slice(1), long: window.__long, attrs: window.__attrs, view } }"""


def analyze(events):
    main_tid = None
    for e in events:
        if e.get("ph") == "M" and e.get("name") == "thread_name" and e["args"].get("name") == "CrRendererMain":
            main_tid = (e["pid"], e["tid"])
    tasks = [e for e in events if e.get("ph") == "X" and (e["pid"], e["tid"]) == main_tid
             and e.get("name") in ("ThreadControllerImpl::RunTask", "RunTask") and e.get("dur", 0) > 40000]
    children = [e for e in events if e.get("ph") == "X" and (e["pid"], e["tid"]) == main_tid and e.get("name") in CHILD]
    nested = [e for e in events if e.get("ph") == "X" and (e["pid"], e["tid"]) == main_tid
              and e.get("name") not in ("ThreadControllerImpl::RunTask", "RunTask") and e.get("dur", 0) > 2000]
    raster = sum(e.get("dur", 0) for e in events if e.get("ph") == "X" and e.get("name") == "RasterTask") / 1000
    rows = []
    for task in sorted(tasks, key=lambda t: -t["dur"])[:6]:
        start, end = task["ts"], task["ts"] + task["dur"]
        parts = {}
        for c in nested:
            if start <= c["ts"] < end:
                parts[c["name"]] = parts.get(c["name"], 0) + c.get("dur", 0) / 1000
        top = ", ".join(f"{k} {v:.0f}" for k, v in sorted(parts.items(), key=lambda kv: -kv[1])[:9])
        rows.append(f"    task {task['dur'] / 1000:.0f} ms: {top}")
    totals = {}
    for c in children:
        totals[c["name"]] = totals.get(c["name"], 0) + c.get("dur", 0) / 1000
    return raster, rows, totals


async def scenario(browser, context, label, action):
    page = await context.new_page()
    cdp = await context.new_cdp_session(page)
    await page.goto(BASE + "/", wait_until="networkidle")
    await page.wait_for_selector("[data-map-surface] svg path")
    await page.wait_for_timeout(2000)
    await cdp.send("Emulation.setCPUThrottlingRate", {"rate": CPU})
    box = await page.locator("[data-map-surface]").bounding_box()
    await page.mouse.move(box["x"] + box["width"] * 0.42, box["y"] + box["height"] * 0.55)
    await page.wait_for_timeout(300)
    await browser.start_tracing(page=page, categories=CATEGORIES)
    await page.evaluate(INSTRUMENT)
    await action(page)
    await page.wait_for_timeout(600)
    rec = await page.evaluate(STOP)
    events = json.loads(await browser.stop_tracing())["traceEvents"]
    raster, rows, totals = analyze(events)
    frames = sorted(rec["frames"])
    p95 = frames[int(len(frames) * 0.95)] if frames else 0
    print(f"\n### {label}  (CPU x{CPU:g}, DPR {DPR:g}; final view {rec['view']})")
    print(f"  frames {len(frames)}, median {statistics.median(frames):.0f}, p95 {p95:.0f}, max {max(frames):.0f} ms, "
          f">50ms {sum(f > 50 for f in frames)}, >100ms {sum(f > 100 for f in frames)}")
    print(f"  long tasks {len(rec['long'])}: {sorted(rec['long'], reverse=True)[:8]}")
    print(f"  attribute mutations: {rec['attrs']}")
    print("  main thread totals: " + ", ".join(f"{k} {v:.0f}" for k, v in sorted(totals.items(), key=lambda kv: -kv[1]) if v >= 5))
    print(f"  raster total {raster:.0f} ms")
    print("  longest tasks:")
    print("\n".join(rows) if rows else "    none > 40 ms")
    await page.close()


async def mouse_bursts(page):
    for direction in (-1, 1):
        for _ in range(5):
            for _ in range(3):
                await page.mouse.wheel(0, 100 * direction)
                await page.wait_for_timeout(50)
            await page.wait_for_timeout(300)


async def trackpad(page):
    for direction in (-1, 1):
        for _ in range(70):
            await page.mouse.wheel(0, 6 * direction)
            await page.wait_for_timeout(16)
        await page.wait_for_timeout(400)


async def buttons(page):
    zoom_in = page.locator("button[aria-label]").filter(has=page.locator("svg")).nth(0)
    labels = await page.evaluate("() => [...document.querySelectorAll('button[aria-label]')].map((b) => b.getAttribute('aria-label'))")
    plus = [label for label in labels if "иблиз" in label or "величить" in label]
    minus = [label for label in labels if "тдал" in label or "меньш" in label]
    for _ in range(4):
        await page.get_by_role("button", name=plus[0]).click()
        await page.wait_for_timeout(450)
    for _ in range(4):
        await page.get_by_role("button", name=minus[0]).click()
        await page.wait_for_timeout(450)
    del zoom_in


async def synthetic(page):
    await page.locator("[data-map-surface]").evaluate("""async (element) => {
      const rect = element.getBoundingClientRect()
      for (let i = 0; i < 180; i++) {
        await new Promise(requestAnimationFrame)
        element.dispatchEvent(new WheelEvent('wheel', { deltaY: i < 90 ? -16 : 16, bubbles: true, cancelable: true,
          clientX: rect.x + rect.width * 0.5, clientY: rect.y + rect.height * 0.55 }))
      }
    }""")


async def main():
    only = sys.argv[1:] or ["mouse", "trackpad", "buttons"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME, headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=DPR)
        print(f"Chromium {browser.version} against {BASE}")
        if "mouse" in only:
            await scenario(browser, context, "mouse wheel: 5 bursts x 3 notches in, then out, 300 ms pauses", mouse_bursts)
        if "trackpad" in only:
            await scenario(browser, context, "trackpad: 70 x deltaY 6 in, pause, 70 out", trackpad)
        if "synthetic" in only:
            await scenario(browser, context, "synthetic: 180 wheel events, one per frame", synthetic)
        if "buttons" in only:
            await scenario(browser, context, "zoom buttons: 4 in, 4 out", buttons)
        await browser.close()


asyncio.run(main())
