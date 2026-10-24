"""HackSphere evaluator and CSV CLI backed exclusively by published QuickML."""

import argparse
from functools import lru_cache
import os
from pathlib import Path
import sys
import tempfile

import numpy as np
import pandas as pd
import requests

from energy.config import QuickMLSettings
from energy.features import build_features
from energy.quickml import QuickMLClient
from energy.validation import parse_telemetry


@lru_cache(maxsize=1)
def get_client() -> QuickMLClient:
    return QuickMLClient(QuickMLSettings.from_env())


def predict(input_df: pd.DataFrame):
    """Return one real cloud prediction per input row, preserving source order."""
    if not isinstance(input_df, pd.DataFrame):
        raise ValueError('predict requires a pandas DataFrame.')
    rows = parse_telemetry(input_df).require_valid()
    return np.asarray(get_client().predict_rows(build_features(rows)), dtype=float)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Predict demand using Voltide QuickML.')
    parser.add_argument('--input', required=True, type=Path, help='Input weather CSV')
    parser.add_argument('--output', required=True, type=Path, help='Complete prediction CSV')
    args = parser.parse_args(argv)
    temporary = None
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError('Input and output paths must differ.')
        source = pd.read_csv(args.input, encoding='utf-8-sig', dtype={'timestamp': str})
        predictions = predict(source)
        rows = parse_telemetry(source).require_valid()
        result = pd.DataFrame({'timestamp': [row.timestamp for row in rows],
                               'target_demand_kw': predictions})
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                dir=args.output.parent, prefix=args.output.name + '.', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            result.to_csv(handle, index=False)
        os.replace(temporary, args.output)
        temporary = None
    except (OSError, ValueError, requests.RequestException):
        print('Prediction failed. Check input, private configuration, and QuickML availability. '
              'No output was replaced.', file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f'Wrote {len(result)} real QuickML predictions to {args.output}.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
