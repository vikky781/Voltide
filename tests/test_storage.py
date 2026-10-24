from copy import deepcopy
import json
from unittest.mock import Mock
from uuid import uuid4

import pytest


SCOPE = 'a' * 64
OTHER_SCOPE = 'b' * 64


def run_fixture():
    return {'run_id': str(uuid4()), 'model_version': 'cloud:V1', 'feature_version': 'v1',
        'generated_at': '2026-10-24T12:00:00+00:00', 'saved': False, 'warnings': [],
        'battery_provenance': 'SIMULATED', 'battery_settings': {},
        'summary': {'peak_demand_kw': 200.0, 'critical_hours': 1},
        'hourly': [{'timestamp': '2015-01-01 00:00:00', 'target_demand_kw': 200.0},
                   {'timestamp': '2015-01-01 23:00:00', 'target_demand_kw': 100.0}]}


def repository():
    from energy.storage import RunRepository
    bucket, table, query = Mock(), Mock(), Mock()
    bucket.put_object.return_value = True
    table.insert_row.side_effect = lambda row: {'ROWID': '1', **row}
    return RunRepository(bucket=bucket, table=table, query=query), bucket, table, query


def test_save_object_before_index_preserves_raw_and_corrected_provenance():
    repo, bucket, table, query = repository()
    events = []
    bucket.put_object.side_effect = lambda *_args, **_kwargs: events.append('object') or True
    table.insert_row.side_effect = lambda row: events.append('index') or {'ROWID': '1', **row}
    run = run_fixture()
    original = deepcopy(run)
    raw = [{'timestamp': '2015-01-01 00:00:00', 'ambient_temp_c': ''}]
    validated = [{'position': 0, 'timestamp': '2015-01-01 00:00:00', 'ambient_temp_c': 25}]
    assert repo.save_run(SCOPE, run, raw, validated) is True
    assert events == ['object', 'index']
    key, body, options = bucket.put_object.call_args.args
    assert options['content_type'] == 'application/json'
    assert key == f'runs/{SCOPE}/{run["run_id"]}.json'
    document = json.loads(body)
    assert document['source_rows'] == raw
    assert document['validated_rows'] == validated
    assert document['result']['saved'] is True
    assert run == original
    metadata = table.insert_row.call_args.args[0]
    assert metadata['session_hash'] == SCOPE and metadata['object_key'] == key
    query.execute_query.return_value = [{'ForecastRuns': metadata}]
    bucket.get_object.return_value = body.encode()
    # A fresh repository object uses the cloud boundary, not an in-process run cache.
    from energy.storage import RunRepository
    reloaded = RunRepository(bucket=bucket, table=table, query=query).get_run(SCOPE, run['run_id'])
    assert reloaded == document['result']


@pytest.mark.parametrize('boundary', ['object', 'index'])
def test_failed_save_does_not_advertise_success(boundary, caplog):
    repo, bucket, table, _ = repository()
    (bucket.put_object if boundary == 'object' else table.insert_row).side_effect = RuntimeError('private upstream body')
    assert repo.save_run(SCOPE, run_fixture(), [], []) is False
    assert 'private upstream body' not in caplog.text
    if boundary == 'object':
        table.insert_row.assert_not_called()


def test_cross_session_lookup_never_reads_the_object_even_with_wrong_query_result():
    repo, bucket, table, query = repository()
    run = run_fixture()
    assert repo.save_run(SCOPE, run, [], [])
    metadata = table.insert_row.call_args.args[0]
    query.execute_query.return_value = [{'ForecastRuns': metadata}]
    assert repo.get_run(OTHER_SCOPE, run['run_id']) is None
    bucket.get_object.assert_not_called()
    assert OTHER_SCOPE in query.execute_query.call_args.args[0]


def test_history_returns_only_own_newest_twenty_summaries_without_storage_identifiers():
    repo, _, _, query = repository()
    rows = [{'session_hash': SCOPE, 'run_id': str(uuid4()), 'created_at': f'2026-10-{day:02d}T12:00:00+00:00',
             'object_key': 'private', 'peak_demand_kw': 200, 'critical_count': 1,
             'first_timestamp': '2015-01-01 00:00:00', 'last_timestamp': '2015-01-01 23:00:00',
             'model_version': 'model', 'feature_version': 'v1'} for day in range(1, 23)]
    query.execute_query.return_value = [{'ForecastRuns': row} for row in [
        *rows, {**rows[-1], 'session_hash': OTHER_SCOPE}]]
    result = repo.list_runs(SCOPE)
    assert len(result) == 20 and result[0]['created_at'] > result[-1]['created_at']
    assert all('session_hash' not in row and 'object_key' not in row for row in result)
    statement = query.execute_query.call_args.args[0]
    assert SCOPE in statement and 'ORDER BY' in statement and 'LIMIT 20' in statement


@pytest.mark.parametrize('identifier', ["x' OR 1=1", '../../secret', 'not-a-uuid'])
def test_malformed_identifiers_never_reach_storage(identifier):
    repo, bucket, _, query = repository()
    assert repo.get_run(SCOPE, identifier) is None
    query.execute_query.assert_not_called()
    bucket.get_object.assert_not_called()


def test_corrupt_object_and_read_failures_are_sanitized():
    from energy.storage import StorageUnavailable
    repo, bucket, table, query = repository()
    run = run_fixture()
    repo.save_run(SCOPE, run, [], [])
    query.execute_query.return_value = [{'ForecastRuns': table.insert_row.call_args.args[0]}]
    bucket.get_object.return_value = b'not-json private body'
    with pytest.raises(StorageUnavailable) as error:
        repo.get_run(SCOPE, run['run_id'])
    assert 'private' not in str(error.value)
    query.execute_query.side_effect = RuntimeError('private body')
    with pytest.raises(StorageUnavailable):
        repo.list_runs(SCOPE)
