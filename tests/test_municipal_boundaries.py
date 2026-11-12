from synthetic_traffic.municipal_boundaries import MunicipalHandler


def test_only_complete_original_admin6_relation_is_emitted():
    source = b"""<osm version="0.6"><node id="1" lat="0" lon="0"/><node id="2" lat="0" lon="1"/><node id="3" lat="1" lon="1"/><node id="4" lat="1" lon="0"/><way id="10"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="4"/><nd ref="1"/></way><relation id="20"><member type="way" ref="10" role="outer"/><tag k="type" v="boundary"/><tag k="boundary" v="administrative"/><tag k="admin_level" v="6"/><tag k="name" v="District"/></relation><relation id="21"><member type="way" ref="99" role="outer"/><tag k="type" v="boundary"/><tag k="boundary" v="administrative"/><tag k="admin_level" v="6"/><tag k="name" v="Missing"/></relation><relation id="22"><member type="way" ref="10" role="outer"/><tag k="type" v="boundary"/><tag k="boundary" v="administrative"/><tag k="admin_level" v="8"/><tag k="name" v="Settlement"/></relation></osm>"""
    handler = MunicipalHandler()
    handler.apply_buffer(source, "osm", locations=True)
    assert set(handler.expected) == {20, 21}
    assert set(handler.polygons) == {20}
    assert handler.polygons[20][0].area == 1
    assert handler.polygons[20][1]["name"] == "District"
