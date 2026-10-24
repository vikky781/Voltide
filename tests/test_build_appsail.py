import json

import pytest


def test_bundle_whitelist_excludes_source_data_credentials_and_development_files(tmp_path):
    from tools.build_appsail import build_bundle

    for directory in ['energy', 'web', 'frontend/dist/assets']:
        (tmp_path / directory).mkdir(parents=True)
    for path in ['energy/__init__.py', 'energy/validation.py', 'web/app.py',
                 'frontend/dist/index.html', 'frontend/dist/assets/app.js', 'requirements.txt', 'requirements-hosted.txt']:
        (tmp_path / path).write_text('safe content')
    for path in ['.env', 'train_telemetry.csv', 'sample_test_input.csv', 'energy/private.key',
                 'energy/ignored.pyc']:
        (tmp_path / path).write_text('private content')
    bundle = build_bundle(tmp_path)
    assert (bundle / 'energy/validation.py').is_file()
    assert (bundle / 'frontend/dist/index.html').is_file()
    assert not any('private content' in path.read_text() for path in bundle.rglob('*') if path.is_file())
    assert not (bundle / 'train_telemetry.csv').exists()
    assert not (bundle / '.env').exists()


def test_missing_frontend_refuses_to_destroy_existing_bundle(tmp_path):
    from tools.build_appsail import build_bundle

    previous = tmp_path / 'artifacts/deploy/previous'
    previous.parent.mkdir(parents=True)
    previous.write_text('keep')
    with pytest.raises(ValueError, match='frontend'):
        build_bundle(tmp_path)
    assert previous.read_text() == 'keep'


def test_private_config_is_separate_from_build_and_rejects_missing_credentials(tmp_path):
    from tools.build_appsail import private_config

    template = {'stack': 'python_3_12', 'command': 'safe command', 'env_variables': {}}
    (tmp_path / 'app-config.json').write_text(json.dumps(template))
    with pytest.raises(ValueError, match='Missing'):
        private_config(tmp_path, {})
    assert not (tmp_path / 'artifacts/appsail/app-config.json').exists()
    env = {key: 'secret-value' for key in ['QUICKML_ENDPOINT_URL', 'QUICKML_ENDPOINT_KEY',
        'QUICKML_MODEL_VERSION', 'CATALYST_ORG_ID', 'CATALYST_PROJECT_ID', 'ZOHO_CLIENT_ID',
        'ZOHO_CLIENT_SECRET', 'ZOHO_REFRESH_TOKEN', 'SESSION_SECRET']}
    env['UNRELATED_CREDENTIAL'] = 'must-not-copy'
    path = private_config(tmp_path, env)
    body = json.loads(path.read_text())
    assert 'UNRELATED_CREDENTIAL' not in body['env_variables']
    assert body['env_variables']['SESSION_SECRET'] == 'secret-value'
    assert body['build_path'] == '../deploy'
    assert json.loads((tmp_path / 'app-config.json').read_text()) == template
