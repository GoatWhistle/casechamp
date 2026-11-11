import re

POLICY = "narrow_unknown_lanes_v1"


def lane_view_sql(database: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", database):
        raise ValueError("Invalid database identifier")
    eligible = """a.lanes_status='missing'
        AND a.highway!='ferry'
        AND a.oneway IN ('forward','reverse','bidirectional','unknown')
        AND NOT has(a.quality,'source_tags:invalid')
        AND NOT match(a.source_tags,'"lanes[^" ]*:conditional"')"""
    return f"""CREATE VIEW IF NOT EXISTS {database}.road_attributes_effective AS
        SELECT a.*,
            ({eligible}) AS lanes_assumed,
            if(lanes_assumed,'{POLICY}',
               if(a.lanes_status='valid','osm','unresolved')) AS lanes_basis,
            if(lanes_assumed,a.oneway='unknown',false) AS bidirectional_assumed,
            if(lanes_assumed,
               CAST(if(a.oneway IN ('forward','reverse'),1,2) AS Nullable(UInt16)),
               a.lanes_total) AS effective_lanes_total,
            if(lanes_assumed,CAST(if(a.oneway='reverse',0,1) AS Nullable(UInt16)),
               a.lanes_forward) AS effective_lanes_forward,
            if(lanes_assumed,CAST(if(a.oneway='forward',0,1) AS Nullable(UInt16)),
               a.lanes_backward) AS effective_lanes_backward
        FROM {database}.road_attributes a"""


def initialize_lane_view(store) -> None:
    store.execute(lane_view_sql(store.database))
