---
name: rail-air-scenarios
description: Inspect railway and aviation connections or calculate new services, faster journeys, service removals and airport closures.
---

# Work with rail and aviation

Read `query_atlas(kind=capabilities)` for the active network model. Do not assume the
internal name `road` means roads only: some snapshots include intercity rail/air
there, while `hansen-frequency-v2` excludes them from road scenarios. Use the
returned `intercity_in_road` flag and an appropriate summer/winter scenario otherwise.

`find_transport(kind=services)` reads the routable snapshot, with `network=intercity` and
`mode=rail|air` for market-city pairs. Local seasonal air/water links use `network=local`
and point IDs, in summer/winter. `query_atlas(kind=links)` instead reads the source catalog
with provenance/frequency; a displayed catalog line need not enter this snapshot.
Neither a model matrix pair nor its time proves a current direct flight/train.
Empty search results do not establish the absence of actual service. Listings can
be truncated; resolve the requested endpoints instead of claiming exhaustive coverage.

Use `calculate_scenario(kind=network)` for a joint scenario, optionally combined with
road changes, for 1-6 distinct atlas regions per call. Obtain exact endpoints before removal.
Removing intercity air with `source=city, target=*` models all air connections touching
that city, not every real airport operation in the region. Federal cities are market
endpoints; evaluate relevant atlas regions instead of inventing their region IDs.
Preserve user-selected affected regions; ask if the population scope is ambiguous.

A new connection uses `action=add` and explicit hours in (0,72]. For intercity these
are in-vehicle hours; the model adds rail/air terminal overhead and, depending on
version, assumed waiting. For local links hours already include waiting/overhead.
To replace an existing pair's travel time, submit remove and add together in one
scenario. The tool adds a bidirectional pair; one-way service or frequency/timetable
edits are not currently supported. Do not claim they were changed. A flight number
or train label alone is not a resolved model pair or a travel time.

Use `appraisal` for an economic evaluation of one region, loading `economic-assessment`
for required OD flows, rates and costs. For several regions supply regional inputs
in separate calls. Without monetary inputs still calculate the requested index
scenario; ask for missing economic inputs if rubles were requested. Passenger time
changes follow the multimodal graph; road freight is not rail/air cargo valuation.

Return the real job IDs and assumptions, then use `manage_calculation(kind=status)` to read
results. No source service is actually edited. Do not invent final effects, repeatedly
poll in one turn, or imply live timetable routing. A zero effect can result from
alternative shortest paths; explain that only when the actual result supports it.
