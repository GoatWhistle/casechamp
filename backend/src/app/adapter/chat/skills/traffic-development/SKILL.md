---
name: traffic-development
description: Find road improvements and short new connections, calculate local trip times and regional Plexus index effects, and show the selected roads on the map.
---

# Road development

For requests to improve roads or add connections, call `calculate_scenario` with `kind=traffic_development`.

Choose `bounds` as west,south,east,north, an exact `region` name, or two exact settlement names/IDs in `places`. Resolve ambiguous names with atlas search. `places` uses the first place as the origin and the second as the destination. Default `pair_flow=1000`, `demand_multiplier=1`, `max_projects=3`; retain user-supplied parameters. For one city and its surroundings, resolve its coordinates and select a bounded surrounding area.

The tool prepares traffic, searches small changes and compares their effects internally: one additional lane, a 20% speed increase and a short new connection up to 5 km. The application keeps one compact progress row, then displays the complete result in this reply. Existing changed roads are red; proposed new links are vivid green.

Acknowledge the geographic task briefly, then allow the background work to finish. Lead the completed answer with local trip minutes before/after, the regional index and the best useful road improvement. Name actual roads. A small regional effect can accompany a useful local improvement. Keep prose concise because the application displays the values. Answer questions about methodology when asked. Preserve unavailable values and actual errors; wait for completed results before describing final effects.

Read a saved result with `manage_calculation(kind=status, calculation_id=traffic-ID, calculation_type=traffic)`. Cancel uses `kind=cancel`. Use `recent` when the ID is missing. `kind=traffic_data` provides source information for explicit source questions.
