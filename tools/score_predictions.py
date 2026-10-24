"""Score saved remote predictions against chronological labels; never fit a model."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from tools.prepare_quickml_data import SPLITS


def _number(value, *, nonnegative=False):
    if isinstance(value, bool):
        raise ValueError('Boolean values are not numeric measurements.')
    result = float(value)
    if not math.isfinite(result) or (nonnegative and result < 0):
        raise ValueError('Measurements must be finite; demand must be nonnegative.')
    return result


def score_rows(truth, predictions):
    if not truth or len(truth) != len(predictions):
        raise ValueError('Truth and predictions require equal, nonzero row counts.')
    errors, hot, critical = [], [], []
    for expected, predicted in zip(truth, predictions):
        if expected['timestamp'] != predicted['timestamp']:
            raise ValueError('Prediction timestamps must exactly match truth in supplied order.')
        actual = _number(expected['target_demand_kw'], nonnegative=True)
        value = _number(predicted['target_demand_kw'], nonnegative=True)
        temperature = _number(expected['ambient_temp_c'])
        error = value - actual
        errors.append(error)
        if temperature >= 30:
            hot.append(error)
        if actual >= 200:
            critical.append(error)

    def metrics(values):
        if not values:
            return dict(count=0, rmse_kw=None, mae_kw=None, bias_kw=None)
        return dict(count=len(values), rmse_kw=math.sqrt(math.fsum(e * e for e in values) / len(values)),
                    mae_kw=math.fsum(abs(e) for e in values) / len(values),
                    bias_kw=math.fsum(values) / len(values))

    return {'all': metrics(errors), 'hot_weather_ge_30c': metrics(hot),
            'actual_demand_ge_200kw': metrics(critical)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--truth', type=Path, default=Path('train_telemetry.csv'))
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--partition', choices=['selection', 'locked_test'], required=True)
    parser.add_argument('--model-version', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists. Preserve evaluation records; choose a new record for a new selection experiment.')
    source = args.truth.read_bytes()
    with args.truth.open(encoding='utf-8-sig', newline='') as handle:
        truth = list(csv.DictReader(handle))
    if len(truth) != 4000:
        parser.error('Expected the supplied 4,000-row labeled source.')
    first, end = SPLITS[args.partition]
    with args.predictions.open(encoding='utf-8-sig', newline='') as handle:
        predictions = list(csv.DictReader(handle))
    rows = truth[first:end]
    report = dict(model_version=args.model_version, feature_version='v1', partition=args.partition,
                  source_sha256=hashlib.sha256(source).hexdigest(),
                  predictions_sha256=hashlib.sha256(args.predictions.read_bytes()).hexdigest(),
                  source_rows=[first + 1, end], first_timestamp=rows[0]['timestamp'],
                  last_timestamp=rows[-1]['timestamp'], metrics=score_rows(rows, predictions))
    content = json.dumps(report, indent=2, allow_nan=False) + '\n'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as handle:
        handle.write(content)
    print(content, end='')


if __name__ == '__main__':
    main()
