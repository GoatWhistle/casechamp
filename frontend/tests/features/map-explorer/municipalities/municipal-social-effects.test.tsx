import { render, screen, within } from "@testing-library/react"
import { expect, it } from "vitest"
import { MunicipalSocialEffects } from "@/features/map-explorer/municipalities/social/municipal-social-effects"
import { LocaleProvider } from "@/shared/i18n"
import ru from "@/shared/i18n/locales/ru/map.json"

const defaults = {
  status: "unavailable",
  reason: null,
  reference_points: 0,
  unresolved_points: 0,
  lost_routes: 0,
  restored_routes: 0,
  delayed_points: 0,
  crossed_threshold_points: 0,
  before_within: 0,
  after_within: 0,
  attached_facilities: 0,
  unattached_facilities: 0,
  points: [],
  method: "test",
  legal_compliance_confirmed: false,
}

it("keeps unavailable calculations distinct from zero harm and exposes method help", () => {
  render(
    <LocaleProvider>
      <MunicipalSocialEffects
        rows={[
          {
            ...defaults,
            criterion_id: "N01",
            threshold_minutes: 60,
            status: "available",
            lost_routes: 0,
            delayed_points: 7,
            crossed_threshold_points: 2,
            reference_points: 20,
            unresolved_points: 3,
          },
          { ...defaults, criterion_id: "N05", threshold_minutes: 15, status: "unavailable" },
        ]}
      />
    </LocaleProvider>,
  )
  const rows = screen.getAllByRole("row")
  const available = rows[1]
  const unavailable = rows[2]
  expect(available).toBeDefined()
  expect(unavailable).toBeDefined()
  if (!available || !unavailable) throw new Error("Missing service rows")
  expect(
    within(available)
      .getAllByRole("cell")
      .map((cell) => cell.textContent),
  ).toEqual(["0", "7", "2"])
  expect(within(unavailable).queryByText("0")).toBeNull()
  const help = screen.getByRole("button", { name: ru.municipalSocial.title })
  expect(document.getElementById(help.getAttribute("aria-describedby") ?? "")?.textContent).toBe(
    ru.municipalSocial.help,
  )
})

it("does not imply social recalculation for historical results", () => {
  const { container } = render(
    <LocaleProvider>
      <MunicipalSocialEffects rows={[]} />
    </LocaleProvider>,
  )
  expect(container.textContent).toBe("")
})
