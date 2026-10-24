from copy import deepcopy
import csv
from io import StringIO

from energy.forecast import ForecastService
from test_api import RemoteFixture, source
from web.app import create_app


class RepositoryBoundaryFixture:
    def __init__(self, succeed=True):
        self.succeed = succeed
        self.documents = {}
        self.sources = []

    def save_run(self, scope, run, raw, validated):
        self.sources.append((scope, deepcopy(raw), deepcopy(validated)))
        if not self.succeed:
            return False
        self.documents[(scope, run['run_id'])] = {**deepcopy(run), 'saved': True}
        return True

    def get_run(self, scope, run_id):
        return deepcopy(self.documents.get((scope, run_id)))

    def list_runs(self, scope):
        return [{'run_id': identifier} for owner, identifier in self.documents if owner == scope]


def application(repo):
    app = create_app(service=ForecastService(RemoteFixture()), repository_factory=lambda _request: repo)
    app.config['TESTING'] = True
    return app


def forecast(client):
    rows = source(25)
    rows[1]['ambient_temp_c'] = ''
    return client.post('/api/forecast', json={'source_rows': rows, 'window_start': rows[1]['timestamp']})


def test_saved_run_preserves_original_source_and_only_its_browser_can_read_or_export():
    repo = RepositoryBoundaryFixture()
    app = application(repo)
    owner, stranger = app.test_client(), app.test_client()
    response = forecast(owner)
    assert response.status_code == 200 and response.json['saved'] is True
    identifier = response.json['run_id']
    assert not any('not saved' in item for item in response.json['warnings'])
    scope, raw, validated = repo.sources[0]
    assert len(scope) == 64 and raw[1]['ambient_temp_c'] == ''
    assert validated[1]['ambient_temp_c'] == 26 and validated[1]['position'] == 1
    assert owner.get('/api/runs').json['runs'] == [{'run_id': identifier}]
    assert len(owner.get(f'/api/runs/{identifier}').json['hourly']) == 24
    assert stranger.get('/api/runs').json['runs'] == []
    assert stranger.get(f'/api/runs/{identifier}').status_code == 404
    assert stranger.get(f'/api/runs/{identifier}/export').status_code == 404
    for kind in ['predictions', 'dispatch']:
        exported = owner.get(f'/api/runs/{identifier}/export?kind={kind}')
        assert exported.status_code == 200
        rows = list(csv.DictReader(StringIO(exported.get_data(as_text=True))))
        assert len(rows) == 24 and rows[0]['timestamp'] == '2015-01-01 01:00:00'
        if kind == 'predictions':
            assert list(rows[0]) == ['timestamp', 'target_demand_kw']
        else:
            assert rows[17]['requested_mode'] == 'RENEWABLE_STORAGE'
            assert 'battery_soc_end_pct' in rows[0] and 'PEAK_WINDOW' in rows[17]['reasons']
        assert 'attachment;' in exported.headers['Content-Disposition']
        assert exported.headers['Cache-Control'] == 'no-store'
    assert owner.get(f'/api/runs/{identifier}/export?kind=bad').status_code == 400


def test_cloud_boundary_failure_keeps_complete_forecast_with_explicit_unsaved_warning():
    client = application(RepositoryBoundaryFixture(succeed=False)).test_client()
    result = forecast(client)
    assert result.status_code == 200 and result.json['saved'] is False
    assert len(result.json['hourly']) == 24
    assert any('could not be saved' in message for message in result.json['warnings'])
    assert client.get('/api/runs').json['runs'] == []


def test_repository_initialization_failure_is_visible_and_does_not_replace_model_results():
    def unavailable(_request):
        raise RuntimeError('private credentials')
    app = create_app(service=ForecastService(RemoteFixture()), repository_factory=unavailable)
    client = app.test_client()
    result = forecast(client)
    assert result.status_code == 200 and result.json['saved'] is False
    history = client.get('/api/runs')
    assert history.status_code == 503 and 'private' not in history.get_data(as_text=True)


def test_signed_session_can_read_saved_run_after_application_restart(monkeypatch):
    monkeypatch.setenv('SESSION_SECRET', 'stable-test-session-secret-only')
    repo = RepositoryBoundaryFixture()
    client = application(repo).test_client()
    identifier = forecast(client).json['run_id']
    cookie = client.get_cookie('session').value
    restarted_client = application(repo).test_client()
    restarted_client.set_cookie('session', cookie)
    assert restarted_client.get(f'/api/runs/{identifier}').status_code == 200
    assert application(repo).test_client().get(f'/api/runs/{identifier}').status_code == 404


def test_hosted_session_cookie_is_secure_http_only_and_same_site(monkeypatch):
    monkeypatch.setenv('X_ZOHO_CATALYST_LISTEN_PORT', '9000')
    monkeypatch.setenv('VOLTIDE_SESSION_SECRET', 'stable-test-session-secret-only')
    response = application(RepositoryBoundaryFixture()).test_client().get('/api/runs', base_url='https://localhost')
    cookie = response.headers['Set-Cookie']
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=Lax' in cookie
