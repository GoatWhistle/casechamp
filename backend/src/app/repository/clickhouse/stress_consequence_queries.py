POINTS = """
SELECT sum(lost_markets) lost_connections,
       countIf(lost_markets > 0) losing_settlements,
       sumIf(population, lost_markets > 0) losing_residents,
       countIf(delay_minutes >= 30) delay30_points,
       sumIf(population, delay_minutes >= 30) delay30_residents,
       countIf(delay_minutes >= 60) delay60_points,
       sumIf(population, delay_minutes >= 60) delay60_residents,
       countIf(delay_minutes >= 120) delay120_points,
       sumIf(population, delay_minutes >= 120) delay120_residents,
       countIf(arrayExists((a,b) -> a <= 2 AND (isNull(b) OR ifNull(b > 2, 0)),
                           before_hours, after_hours)) crossing_points,
       sumIf(population, arrayExists((a,b) -> a <= 2 AND (isNull(b) OR ifNull(b > 2, 0)),
                                      before_hours, after_hours)) crossing_residents
FROM plexus_state.stress_point_impacts FINAL
WHERE job_id={id:String} AND region={region:String}
"""

CONNECTIONS = """
SELECT point_id, name, population,
       tupleElement(link, 1) destination,
       tupleElement(link, 2) before_h,
       tupleElement(link, 3) after_h
FROM plexus_state.stress_point_impacts FINAL
ARRAY JOIN arrayZip(markets, before_hours, after_hours) AS link
WHERE job_id={id:String} AND region={region:String}
"""

NEARBY = (
    """
SELECT count() changed, countIf(isNull(after_h)) lost,
       countIf(isNotNull(after_h)) comparable,
       sumIf(before_h * 60, isNotNull(after_h)) before_sum,
       sumIf(ifNull(after_h,0) * 60, isNotNull(after_h)) after_sum,
       countIf(isNull(after_h) OR ifNull(after_h > 2,0)) crossing
FROM ("""
    + CONNECTIONS
    + ") WHERE before_h <= 2"
)

DESTINATIONS = (
    """
SELECT destination, count() settlements, sum(population) residents,
       countIf(isNull(after_h)) lost,
       sumIf(population, isNull(after_h)) lost_residents,
       sumIf(population, before_h <= 2) nearby_residents,
       countIf(isNotNull(after_h)) comparable,
       sumIf(before_h * 60, isNotNull(after_h)) before_sum,
       sumIf(ifNull(after_h,0) * 60, isNotNull(after_h)) after_sum
FROM ("""
    + CONNECTIONS
    + """ )
GROUP BY destination
ORDER BY nearby_residents DESC, lost_residents DESC, residents DESC, destination
LIMIT 5
"""
)

EXAMPLES = (
    """
SELECT point_id, name, population, destination, before_h * 60 before_minutes,
       after_h * 60 after_minutes, (after_h - before_h) * 60 added_minutes
FROM ("""
    + CONNECTIONS
    + """ )
ORDER BY isNull(after_h) DESC, (before_h <= 2) DESC, population DESC,
         added_minutes DESC, point_id, destination
LIMIT 3 BY isNull(after_h)
LIMIT 6
"""
)
