import math

import pytest

from tools.score_predictions import score_rows


def records():
    truth = [dict(timestamp=f'2015-01-01 {hour:02}:00:00', ambient_temp_c=temp,
                  target_demand_kw=value) for hour, temp, value in [(0, 20, 100), (1, 32, 200)]]
    predictions = [dict(timestamp=row['timestamp'], target_demand_kw=value)
                   for row, value in zip(truth, [103, 196])]
    return truth, predictions


def test_hand_checked_metrics_and_populated_subsets():
    truth, predictions = records()
    result = score_rows(truth, predictions)
    assert result['all'] == {'count': 2, 'rmse_kw': math.sqrt(12.5), 'mae_kw': 3.5, 'bias_kw': -0.5}
    assert result['hot_weather_ge_30c']['rmse_kw'] == 4
    assert result['actual_demand_ge_200kw']['bias_kw'] == -4


def test_empty_subsets_are_explicitly_unscored():
    truth, predictions = records()
    result = score_rows(truth[:1], predictions[:1])
    assert result['hot_weather_ge_30c'] == {'count': 0, 'rmse_kw': None, 'mae_kw': None, 'bias_kw': None}


@pytest.mark.parametrize('change', ['order', 'count', 'nan', 'negative', 'infinite_truth', 'empty'])
def test_invalid_or_misaligned_predictions_fail(change):
    truth, predictions = records()
    if change == 'order': predictions.reverse()
    elif change == 'count': predictions.pop()
    elif change == 'nan': predictions[0]['target_demand_kw'] = float('nan')
    elif change == 'negative': predictions[0]['target_demand_kw'] = -1
    elif change == 'infinite_truth': truth[0]['target_demand_kw'] = float('inf')
    elif change == 'empty': truth, predictions = [], []
    with pytest.raises(ValueError): score_rows(truth, predictions)
