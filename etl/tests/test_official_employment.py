from import_official_employment import facilities_for_region


def test_directory_deduplicates_and_rejects_suspicious_coordinates_and_profiles():
    metadata={'id':'R','source_url':'https://trudvsem.ru/czn','raw_sha256':'a'*64,'retrieved_at':'2026-11-12'}
    valid={'name':'Центр занятости населения','address':'Адрес','latitude':55,'longitude':65}
    records=[valid,dict(valid),{**valid,'address':'Other','longitude':13},{**valid,'name':'Управление социальной защиты'}]
    facilities,quality=facilities_for_region(metadata,records,[60,50,70,60])
    assert len(facilities)==3
    assert facilities[0].latitude==55 and facilities[0].coordinate_status=='official_institution_pin'
    assert all(f.latitude is None and f.coordinate_status=='missing' for f in facilities[1:])
    assert all(f.source_sha256=='a'*64 for f in facilities)
    assert quality=={'duplicates':1,'geometry_rejected':1,'profile_rejected':1}
