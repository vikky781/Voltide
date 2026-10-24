import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests


def settings():
    from energy.config import QuickMLSettings
    return QuickMLSettings(endpoint_url='https://api.catalyst.zoho.in/quickml/v1/project/123/endpoints/predict',
        endpoint_key='private-endpoint', model_version='baseline:V1', org_id='456', project_id='123',
        client_id='private-client', client_secret='private-secret', refresh_token='private-refresh')


def response(body, status=200, headers=None):
    result = Mock(status_code=status, headers=headers or {})
    result.json.return_value = body
    return result


def client_with(responses, **kwargs):
    from energy.quickml import QuickMLClient
    transport = Mock()
    transport.post.side_effect = responses
    return QuickMLClient(settings(), transport=transport, **kwargs), transport


def token():
    return response({'access_token': 'private-access', 'expires_in': 3600})


def test_captured_live_response_and_sequential_chunk_order():
    fixture = json.loads((Path(__file__).parent / 'fixtures/quickml/batch24.json').read_text())
    client, transport = client_with([token(), response(fixture['response']), response({'result': [99]})])
    rows = fixture['request']['data'] + [fixture['request']['data'][0]]
    assert client.predict_rows(rows) == fixture['response']['result'] + [99.0]
    calls = transport.post.call_args_list
    assert calls[1].kwargs['json'] == fixture['request']
    assert calls[2].kwargs['json'] == {'data': [rows[-1]]}
    assert calls[1].kwargs['headers']['Authorization'] == 'Zoho-oauthtoken private-access'
    assert calls[1].kwargs['headers']['CATALYST-ORG'] == '456'
    assert calls[1].kwargs['allow_redirects'] is False
    assert calls[0].kwargs['data']['refresh_token'] == 'private-refresh'
    # A second invocation reuses the unexpired token.
    transport.post.side_effect = [response({'result': [7]})]
    assert client.predict_rows([rows[0]]) == [7.0]
    assert transport.post.call_count == 4


@pytest.mark.parametrize('body', [{}, {'result': []}, {'result': [1, 2]}, {'result': [[1]]},
    {'result': ['1']}, {'result': [True]}, {'result': [-1]}, {'result': [float('nan')]},
    {'result': [float('inf')]}, {'result': [1], 'status': 'error'}])
def test_bad_prediction_never_becomes_fallback(body):
    from energy.contracts import PredictionError
    client, _ = client_with([token(), response(body)])
    with pytest.raises(PredictionError):
        client.predict_rows([{'hour': 0}])


def test_401_refreshes_once_and_replays_same_chunk():
    client, transport = client_with([token(), response({}, 401), token(), response({'result': [8]})])
    assert client.predict_rows([{'hour': 0}]) == [8.0]
    assert transport.post.call_args_list[1].kwargs['json'] == transport.post.call_args_list[3].kwargs['json']


@pytest.mark.parametrize('status', [429, 503])
def test_transient_status_retries_boundedly(status):
    sleeper = Mock()
    client, _ = client_with([token(), response({}, status, {'Retry-After': '2'}),
                            response({'result': [8]})], sleep=sleeper)
    assert client.predict_rows([{'hour': 0}]) == [8.0]
    sleeper.assert_called_once_with(2.0 if status == 429 else 1.0)


@pytest.mark.parametrize('failure', [requests.Timeout('private-secret'),
                                  requests.ConnectionError('private-secret')])
def test_transport_failure_sanitized_after_bounded_retries(failure):
    from energy.contracts import PredictionError
    client, transport = client_with([token(), failure, failure, failure], sleep=Mock())
    with pytest.raises(PredictionError) as error:
        client.predict_rows([{'hour': 0}])
    assert 'private' not in str(error.value)
    assert transport.post.call_count == 4


def test_partial_chunks_are_not_returned_when_later_chunk_fails():
    from energy.contracts import PredictionError
    client, _ = client_with([token(), response({'result': [1]*24}), response({}, 403)])
    with pytest.raises(PredictionError):
        client.predict_rows([{'hour': 0}]*25)


def test_bad_json_and_bad_refresh_are_sanitized():
    from energy.contracts import PredictionError
    malformed = response({})
    malformed.json.side_effect = ValueError('private-response')
    for replies in [[token(), malformed], [response({'error': 'private-response'})]]:
        client, _ = client_with(replies)
        with pytest.raises(PredictionError) as error:
            client.predict_rows([{'hour': 0}])
        assert 'private-response' not in str(error.value)


def test_deadline_stops_before_new_network_request():
    from energy.contracts import PredictionError
    client, transport = client_with([], clock=Mock(side_effect=[0, 121]))
    with pytest.raises(PredictionError, match='deadline'):
        client.predict_rows([{'hour': 0}])
    transport.post.assert_not_called()


def test_configuration_rejects_missing_or_unsafe_destinations():
    from energy.config import QuickMLSettings
    with pytest.raises(ValueError, match='Missing'):
        QuickMLSettings.from_env({})
    from dataclasses import replace
    for change in [{'endpoint_url': 'https://example.com'},
                   {'accounts_url': 'https://example.com'}, {'feature_version': 'v2'}]:
        with pytest.raises(ValueError):
            replace(settings(), **change)
    assert 'private' not in repr(settings())
