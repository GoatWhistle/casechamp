import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
local = {row['id']: row for row in json.loads((OUT / 'local-coverage.json').read_text())}
rows = []
for batch in range(1, 4):
    group = json.loads((OUT / f'findings-{batch}.json').read_text())
    expected = {row['id'] for row in json.loads((OUT / f'batch-{batch}.json').read_text())}
    assert {row['id'] for row in group} == expected
    assert len(group) == len(expected)
    rows.extend(group)
assert len(rows) == 82 and {row['id'] for row in rows} == set(local)
source_count = 0
access = Counter()
for row in rows:
    assert row['name'] == local[row['id']]['name']
    for mode in ('rail', 'air'):
        detail = row[mode]
        assert isinstance(detail['status'], str)
        if mode == 'air':
            assert (detail['status'] == 'already_in_atlas') == (local[row['id']]['atlas_air_links'] > 0)
        for source in detail['sources']:
            assert source['url'].startswith('https://') or source['url'].startswith('http://')
            assert source['title'] and source['evidence']
            assert source.get('access_level')
            source_count += 1
            access[source['access_level']] += 1
rows.sort(key=lambda row: row['name'])
(OUT / 'findings-all.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
summary = {
    'date': '2026-11-10', 'regions': len(rows), 'rail_regions_searched': 82,
    'air_gap_regions_searched': 54, 'source_references': source_count,
    'unique_urls': len({source['url'] for row in rows for mode in ('rail', 'air') for source in row[mode]['sources']}),
    'source_access_levels': dict(access),
    'rail_status_counts': dict(Counter(row['rail']['status'] for row in rows)),
    'air_status_counts': dict(Counter(row['air']['status'] for row in rows)),
    'limitation': 'Source discovery only; not a complete route import or certification of current operation.'
}
(OUT / 'validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
lines = ['# Все 82 региона: состояние данных и найденные источники', '',
         'Проверка 10.11.2026. Числа — записи атласа или исходящие модельные пары, не число рейсов. Статусы поиска сохранены дословно; доказательства, даты и уровень доступа — в findings-all.json. Источник может быть историческим или доступным только в поисковой выдаче.', '',
         '| Регион | Атлас ж/д / авиа | Модель ж/д / авиа | Ж/д: статус и источник | Авиа: статус и источник |',
         '|---|---:|---:|---|---|']
for row in rows:
    count = local[row['id']]
    cells = []
    for mode in ('rail', 'air'):
        detail = row[mode]
        sources = ' '.join(f'[источник {index + 1}]({source["url"]})' for index, source in enumerate(detail['sources']))
        cells.append(detail['status'] + ' ' + sources)
    lines.append(f'| {row["name"]} | {count["atlas_rail_links"]} / {count["atlas_air_links"]} | {count["model_rail_outgoing_pairs"]} / {count["model_air_outgoing_pairs"]} | {cells[0]} | {cells[1]} |')
(OUT / 'all-regions.md').write_text('\n'.join(lines) + '\n')
print(json.dumps(summary, ensure_ascii=False, indent=2))
