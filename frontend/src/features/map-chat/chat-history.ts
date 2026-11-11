import type { ChatEntry } from "./use-map-chat"

export function historyContent(row: ChatEntry): string {
  if (
    !row.scenarios?.length &&
    !row.stressTests?.length &&
    !row.tables.length &&
    !row.mapCommands.length &&
    !row.calculations?.length &&
    !row.analyses?.length
  )
    return row.content.slice(0, 12000)
  const context = {
    scenarios: row.scenarios,
    stress_routes: Object.entries(row.stressRoutes ?? {}).map(([job_id, route]) => ({
      job_id,
      origin: route.origin.id,
      destination: route.destination.id,
    })),
    stress_tests: row.stressTests?.map(({ id }) => ({ id })),
    displayed_tables: row.tables.map((table) => ({
      title: table.title,
      rows: table.rows.map(({ id, name, origin, destination, calculation_id }) => ({
        calculation_id,
        id,
        name,
        origin,
        destination,
      })),
    })),
    analyses: row.analyses?.map(({ id, region_id, mode }) => ({ id, region_id, mode })),
    commentaries: Object.values(row.commentaries ?? {})
      .filter((value) => value.complete)
      .map((value) => value.text.slice(0, 2000)),
    map_commands: row.mapCommands,
    calculations: row.calculations?.map((item) => ({
      corridor_id: item.corridor.id,
      job_ids: item.job_ids,
    })),
  }
  return `${row.content.slice(0, 6000)}\n\nDisplayed data context:\n${JSON.stringify(context)}`.slice(
    0,
    12000,
  )
}

export function historyOf(messages: ChatEntry[]) {
  return messages
    .filter(
      (row) =>
        row.complete &&
        (row.content ||
          row.tables.length ||
          row.mapCommands.length ||
          row.calculations?.length ||
          row.analyses?.length ||
          row.stressTests?.length ||
          row.scenarios?.length),
    )
    .slice(-12)
    .map((row) => ({ role: row.role, content: historyContent(row) }))
}
