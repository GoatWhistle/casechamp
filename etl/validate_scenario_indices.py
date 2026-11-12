import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from analytics.client import ClickHouse
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.scenario_indices import ClickHouseScenarioIndexRepository
from calculate_scenario_indices import calculate

ROOT = Path(__file__).resolve().parents[1]


def main():
    client = ClickHouse()
    reader = ClickHouseReader(os.environ.get('CLICKHOUSE_URL', 'http://127.0.0.1:18123'), os.environ.get('CLICKHOUSE_USER', 'plexus'), os.environ['CLICKHOUSE_PASSWORD'], max_threads=1, max_block_size=8192)
    repository = ClickHouseScenarioIndexRepository(reader)
    results = []
    for criterion in ('N03', 'N05', 'N06', 'N07', 'N08', 'N09'):
        for saved in repository.regions(criterion):
            actual = calculate(client, reader, {'region_id': saved.region_id, 'criterion_id': criterion, 'run_id': saved.run_id})
            if asdict(saved) != asdict(actual):
                raise ValueError(f'Scenario summary differs from stored measurement: {saved.region_id}/{criterion}/{saved.run_id}')
            results.append({'region_id': saved.region_id, 'criterion_id': criterion, 'run_id': saved.run_id, 'reference_points': actual.scenario[0].reference_points, 'thresholds': list(actual.policy.thresholds)})
        print('Validated stored scenario summaries', criterion, len(results), flush=True)
    evidence = {'checked_at': datetime.now(UTC).isoformat(), 'method': 'Reaggregate every currently published scenario from its immutable stored measurement using its frozen run ID and compare all policy, baseline/scenario, count and population fields; verifies aggregation, not geographic or legal correctness', 'checked_summaries': len(results), 'mismatches': 0, 'results': results}
    (ROOT/'docs/results/normative-scenario-reaggregation-validation.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
