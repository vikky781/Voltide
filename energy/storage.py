"""Private Stratus run documents with a session-scoped Data Store index."""

from copy import deepcopy
import json
import logging
import re
from uuid import UUID

logger = logging.getLogger(__name__)


class StorageUnavailable(RuntimeError):
    def __init__(self):
        super().__init__('Forecast history is unavailable. Please try again later.')


SUMMARY_FIELDS = ('run_id', 'created_at', 'first_timestamp', 'last_timestamp',
                  'model_version', 'feature_version', 'peak_demand_kw', 'critical_count')


class RunRepository:
    def __init__(self, *, bucket, table, query, table_name='ForecastRuns'):
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', table_name):
            raise ValueError('Invalid history table name.')
        self.bucket, self.table, self.query = bucket, table, query
        self.table_name = table_name

    @staticmethod
    def _scope(scope):
        if not isinstance(scope, str) or not re.fullmatch(r'[a-f0-9]{64}', scope):
            raise ValueError('Invalid session scope.')

    @staticmethod
    def _valid_id(run_id):
        try:
            return isinstance(run_id, str) and str(UUID(run_id)) == run_id
        except ValueError:
            return False

    def _records(self, statement):
        try:
            rows = self.query.execute_query(statement)
            if not isinstance(rows, list):
                raise ValueError('Invalid history response')
            return [item[self.table_name] for item in rows]
        except Exception:
            raise StorageUnavailable() from None

    def save_run(self, scope, run, source_rows, validated_rows) -> bool:
        stage = 'document'
        try:
            self._scope(scope)
            if not self._valid_id(run['run_id']):
                return False
            key = f'runs/{scope}/{run["run_id"]}.json'
            result = deepcopy(run)
            result['saved'] = True
            document = {'schema_version': 1, 'source_rows': source_rows,
                        'validated_rows': validated_rows, 'result': result}
            body = json.dumps(document, allow_nan=False, separators=(',', ':'))
            stage = 'object upload'
            if self.bucket.put_object(key, body, {'content_type': 'application/json'}) is not True:
                return False
            metadata = {'run_id': run['run_id'], 'session_hash': scope,
                        'created_at': run['generated_at'], 'object_key': key,
                        'first_timestamp': run['hourly'][0]['timestamp'],
                        'last_timestamp': run['hourly'][-1]['timestamp'],
                        'model_version': run['model_version'], 'feature_version': run['feature_version'],
                        'peak_demand_kw': run['summary']['peak_demand_kw'],
                        'critical_count': run['summary']['critical_hours']}
            stage = 'metadata index'
            inserted = self.table.insert_row(metadata)
            return isinstance(inserted, dict) and bool(inserted.get('ROWID'))
        except Exception as error:
            # An index failure may leave a private orphan object; it is never listed as saved.
            logger.warning('Forecast save failed at %s (%s).', stage, type(error).__name__)
            return False

    def list_runs(self, scope):
        self._scope(scope)
        rows = self._records(f"SELECT * FROM {self.table_name} WHERE session_hash = '{scope}' "
                             'ORDER BY created_at DESC LIMIT 20')
        try:
            own_rows = [row for row in rows if row['session_hash'] == scope]
            own_rows.sort(key=lambda row: row['created_at'], reverse=True)
            return [{name: row[name] for name in SUMMARY_FIELDS} for row in own_rows[:20]]
        except (KeyError, TypeError):
            raise StorageUnavailable() from None

    def get_run(self, scope, run_id):
        self._scope(scope)
        if not self._valid_id(run_id):
            return None
        rows = self._records(f"SELECT * FROM {self.table_name} WHERE session_hash = '{scope}' "
                             f"AND run_id = '{run_id}' LIMIT 1")
        if not rows:
            return None
        try:
            metadata = rows[0]
            if metadata['session_hash'] != scope or metadata['run_id'] != run_id:
                return None
            expected_key = f'runs/{scope}/{run_id}.json'
            if metadata['object_key'] != expected_key:
                raise ValueError('Invalid object reference')
            document = json.loads(self.bucket.get_object(expected_key))
            result = document['result']
            if document['schema_version'] != 1 or result['run_id'] != run_id or result['saved'] is not True:
                raise ValueError('Invalid run document')
            return result
        except Exception:
            raise StorageUnavailable() from None


def repository_from_request(request, bucket_name, table_name='ForecastRuns'):
    """Use only Catalyst's request-scoped server credentials, never browser credentials."""
    import zcatalyst_sdk

    app = zcatalyst_sdk.initialize(req=request, scope='admin')
    return RunRepository(bucket=app.stratus().bucket(bucket_name),
                         table=app.datastore().table(table_name), query=app.zcql(),
                         table_name=table_name)
