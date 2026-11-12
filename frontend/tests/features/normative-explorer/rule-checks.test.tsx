import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router"
import { expect, it } from "vitest"
import { NormativeRuleChecks } from "@/features/normative-explorer/normative-rule-checks"
import type { components } from "@/shared/api"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/normative.json"

type Check = components["schemas"]["RuleCheckResponse"]
const unregulated: Check = {
  rule_id: "rngp178_stop_walk",
  applicability: "not_regulated",
  threshold: null,
  unit: "metres",
  measurement: "walking_path",
  value: null,
  result: "not_regulated",
  reason: "rural_not_regulated",
  source_url: "https://example.org/rule",
  edition_date: "2023-02-08",
  facts_source_url: null,
  facts_observed_at: null,
  candidate_thresholds: [],
}

async function show(check: Check) {
  render(
    <MemoryRouter>
      <LocaleProvider>
        <NormativeRuleChecks walking checks={[check]} />
      </LocaleProvider>
    </MemoryRouter>,
  )
  await userEvent.click(screen.getByRole("button", { name: ru.rulesTitle }))
  await userEvent.click(screen.getByRole("button", { name: ru.ruleNames[check.rule_id] }))
}

it("distinguishes an unregulated rural row from an unknown numerical limit", async () => {
  await show(unregulated)
  expect(screen.getByText(ru.ruleResults.not_regulated)).toBeDefined()
  expect(screen.getByText(ru.noNumericalLimit)).toBeDefined()
  expect(screen.queryByText("500")).toBeNull()
  expect(screen.queryByText("0")).toBeNull()
})

it("keeps candidate thresholds separate from a selected unknown threshold", async () => {
  await show({
    ...unregulated,
    applicability: "unknown",
    result: "unknown",
    reason: "zone_unknown",
    candidate_thresholds: [250, 500],
  })
  expect(screen.getByText(ru.ruleResults.unknown)).toBeDefined()
  expect(screen.getByText(ru.ruleReasons.zone_unknown)).toBeDefined()
  expect(screen.queryByText(ru.noNumericalLimit)).toBeNull()
  expect(
    screen.getByText((text) => text.startsWith(ru.ruleCandidates.split("{{values}}")[0] ?? "")),
  ).toBeDefined()
})
