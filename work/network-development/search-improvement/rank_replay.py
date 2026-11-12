import argparse
import json
from hashlib import sha256
from pathlib import Path
from time import monotonic

import numpy as np
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.housing import distribute
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import DemandParameters
from synthetic_traffic.source import load_network, load_places
from synthetic_traffic.surrogate import (
    ARTIFACT, FEATURES, build_feature_context, features, load_surrogate,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    pilot = root / 'work/network-development/llm-pilot-local-diff'
    protocol = json.loads((pilot / 'protocol.json').read_text())
    source = json.loads((pilot / 'result.json').read_text())
    snapshot = Path(protocol['snapshot'])
    network = load_network(snapshot)
    places, _ = load_places(snapshot, network)
    homes, _ = distribute(snapshot / 'housing.parquet', places, network)
    zones, _ = aggregate(homes, network, 2, 128)
    trips, _ = generate(network, zones, DemandParameters())
    baseline = prepare_incremental(network, trips, 300, 1e-3)
    assert baseline.assignment.converged
    population = sum(v['population'] for v in protocol['baseline_indices'])
    before = sum(v['value'] * v['population'] for v in protocol['baseline_indices']) / population
    attempts = [x for x in source['arms'][0]['index_attempts'] if x['status'] == 'index_verified']
    started = monotonic()
    model = load_surrogate()
    context = build_feature_context(network, baseline.assignment)
    rows = [features(network, baseline.assignment, x['project'], context) for x in attempts]
    predicted = model.predict(rows, thread_count=1)
    order = np.argsort(-predicted, kind='stable')
    gains = np.asarray([x['weighted_regional_index'] - before for x in attempts])
    result = {
        'metric': 'population_weighted_selected_region_hansen',
        'artifact_sha256': sha256(ARTIFACT.read_bytes()).hexdigest(),
        'feature_names': FEATURES,
        'ranking_seconds': monotonic() - started,
        'samples': len(attempts),
        'distinct_predictions': len(set(float(x) for x in predicted)),
        'best_known_gain': float(gains.max()),
        'top_k_best_gain': {str(k): float(gains[order[:k]].max()) for k in [1, 3, 5, 10]},
        'ranked': [
            {'source_attempt': int(i), 'kind': attempts[i]['project']['kind'],
             'origins': attempts[i]['origins'], 'predicted_local_gain': float(predicted[i]),
             'verified_index_gain': float(gains[i]), 'features': rows[i]}
            for i in order
        ],
        'limits': [
            'Replay only: candidates already selected by the previous search',
            'Known candidate geometry may occur in new local-label training; not independent holdout',
            'Predictions target local accessibility, labels here are exact regional index',
            'No new exact index runs; runtime throughput not measured by this replay',
        ],
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'ranked'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
