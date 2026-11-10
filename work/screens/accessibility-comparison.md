# Accessibility comparison

Mode: Operate. Regional analysts compare the published method with planned-trip potential on a fixed snapshot.

- Extend the existing region links workspace, using its Card, table, Segmented, Banner, Skeleton and ErrorState primitives and current tokens. No new visual identity or animation.
- Show named summer/winter rows, previous/potential/difference, then removal effects for air/rail/water. Default half-life is 2h; 4h/8h are explicitly sensitivity checks.
- Explain optimistic planned-departure assumptions and incomplete schedules adjacent to results. Frequency counts refer to the national calculation network, not flights operated.
- Loading uses skeleton, failed/unpublished calculation uses retry, stale snapshot remains visibly labelled. Zeros are numbers; unavailable values use NoValue.
- Desktop checks only, per user instruction. Preserve map, chat and other concurrent work.
