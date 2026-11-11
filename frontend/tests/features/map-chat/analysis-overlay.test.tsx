import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { expect, it, vi } from "vitest"
import { AnalysisResults } from "@/features/map-chat/analysis/analysis-results"
import type { AnalysisDetail, AnalysisJob } from "@/shared/api/road-analysis"
import { LocaleProvider } from "@/shared/i18n"

it("shows the selected ranked road on the map and preserves keyboard navigation", async () => {
  const client = new QueryClient({
    defaultOptions: { queries: { staleTime: Infinity, retry: false } },
  })
  const result = {
    candidate: {
      way_id: 42,
      name: "Road",
      length_km: 3,
      score: 1,
      isolation_score: 0,
      crosses_boundary: false,
    },
    before: 100,
    after: 90,
    delta: -10,
    affected_population: 200,
    isolated_population: 0,
    elapsed_seconds: 1,
  }
  const job: AnalysisJob = {
    id: "analysis",
    region_id: "17",
    region: "Region",
    mode: "criticality",
    percent: 20,
    fingerprint: "snapshot",
    status: "paused",
    stage: "verifying",
    candidates: [result.candidate],
    results: [result],
    failures: [],
    candidate_count: 1,
    batch_target: 10,
    current_way_id: null,
    completed: 1,
    total: 1,
    elapsed_seconds: 1,
    error: null,
    compatible: true,
  }
  const detail: AnalysisDetail = {
    result,
    lines: [
      [
        [40, 56],
        [40.1, 56.1],
      ],
    ],
    settlements: [],
  }
  client.setQueryData(["road-analysis-detail", job.id, result.candidate.way_id], detail)
  const onOverlay = vi.fn()
  const view = render(
    <QueryClientProvider client={client}>
      <LocaleProvider>
        <AnalysisResults job={job} onOverlay={onOverlay} />
      </LocaleProvider>
    </QueryClientProvider>,
  )
  expect(onOverlay).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole("button"), { detail: 0 })
  await waitFor(() =>
    expect(onOverlay).toHaveBeenCalledWith({ detail, focus: expect.any(Number), instant: true }),
  )
  fireEvent.click(screen.getByRole("button"), { detail: 1 })
  await waitFor(() => expect(onOverlay).toHaveBeenCalledTimes(2))
  expect(onOverlay.mock.lastCall?.[0].instant).toBe(false)
  view.unmount()
  client.clear()
})
