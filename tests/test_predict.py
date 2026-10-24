from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest


@pytest.mark.parametrize('count', [1, 24, 25, 1000])
def test_evaluator_preserves_count_input_order_duplicates_and_input_frame(monkeypatch, count):
    import predict as module

    source = pd.read_csv('sample_test_input.csv').iloc[:count].copy()
    if count > 1:
        source = source.iloc[::-1].reset_index(drop=True)
        source.loc[1, 'timestamp'] = source.loc[0, 'timestamp']
    original = source.copy(deep=True)
    remote = Mock()
    remote.predict_rows.side_effect = lambda rows: [row['ambient_temp_c'] for row in rows]
    monkeypatch.setattr(module, 'get_client', lambda: remote)
    result = module.predict(source)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, source.ambient_temp_c.to_numpy())
    pd.testing.assert_frame_equal(original, source)
    assert all('timestamp' not in row and 'target_demand_kw' not in row
               for row in remote.predict_rows.call_args.args[0])


def test_invalid_input_never_calls_remote(monkeypatch):
    import predict as module
    remote = Mock()
    monkeypatch.setattr(module, 'get_client', lambda: remote)
    with pytest.raises(ValueError):
        module.predict(pd.DataFrame([{'timestamp': 'bad'}]))
    remote.predict_rows.assert_not_called()


def test_cli_output_is_complete_atomic_and_preserves_timestamp_text(tmp_path, monkeypatch):
    import predict as module
    source = tmp_path / 'source.csv'
    out = tmp_path / 'out.csv'
    frame = pd.read_csv('sample_test_input.csv').iloc[:2]
    frame.to_csv(source, index=False)
    monkeypatch.setattr(module, 'predict', lambda df: np.array([101.5, 202.75]))
    assert module.main(['--input', str(source), '--output', str(out)]) == 0
    result = pd.read_csv(out)
    assert list(result.columns) == ['timestamp', 'target_demand_kw']
    assert result.timestamp.tolist() == frame.timestamp.tolist()
    assert result.target_demand_kw.tolist() == [101.5, 202.75]
    original = out.read_bytes()
    monkeypatch.setattr(module, 'predict', Mock(side_effect=ValueError('Model unavailable')))
    assert module.main(['--input', str(source), '--output', str(out)]) == 1
    assert out.read_bytes() == original
    assert not list(tmp_path.glob('*.tmp'))
