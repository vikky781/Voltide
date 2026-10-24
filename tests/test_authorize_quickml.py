from unittest.mock import Mock

import pytest
from dotenv import dotenv_values


def test_exchange_uses_post_body_and_saves_only_refresh_token(tmp_path):
    from tools.authorize_quickml import exchange_grant

    env = tmp_path / '.env'
    env.write_text('ZOHO_CLIENT_ID=client\nZOHO_CLIENT_SECRET=secret\nOTHER=keep\n')
    transport = Mock()
    transport.post.return_value.status_code = 200
    transport.post.return_value.json.return_value = {
        'access_token': 'temporary', 'refresh_token': 'refresh', 'expires_in': 3600}
    exchange_grant('short-lived-code', env, transport)
    args, kwargs = transport.post.call_args
    assert args == ('https://accounts.zoho.in/oauth/v2/token',)
    assert kwargs['data'] == {'client_id': 'client', 'client_secret': 'secret',
                             'grant_type': 'authorization_code', 'code': 'short-lived-code'}
    assert kwargs['allow_redirects'] is False
    assert kwargs['timeout'] == 30
    saved = dotenv_values(env)
    assert saved['ZOHO_REFRESH_TOKEN'] == 'refresh'
    assert saved['OTHER'] == 'keep'
    assert 'temporary' not in env.read_text()
    assert 'short-lived-code' not in env.read_text()


@pytest.mark.parametrize('response', [{'error': 'invalid_code'}, {'access_token': 'only-access'}])
def test_failed_exchange_does_not_change_credentials_or_expose_response(tmp_path, response):
    from tools.authorize_quickml import exchange_grant

    env = tmp_path / '.env'
    original = 'ZOHO_CLIENT_ID=client\nZOHO_CLIENT_SECRET=secret\n'
    env.write_text(original)
    transport = Mock()
    transport.post.return_value.status_code = 200
    transport.post.return_value.json.return_value = response
    with pytest.raises(ValueError, match='grant exchange failed'):
        exchange_grant('code', env, transport)
    assert env.read_text() == original


def test_non_zoho_destination_rejected_before_transmitting_secrets(tmp_path):
    from tools.authorize_quickml import exchange_grant

    env = tmp_path / '.env'
    env.write_text('ZOHO_CLIENT_ID=client\nZOHO_CLIENT_SECRET=secret\n'
                   'ZOHO_ACCOUNTS_URL=https://example.com\n')
    transport = Mock()
    with pytest.raises(ValueError, match='India'):
        exchange_grant('code', env, transport)
    transport.post.assert_not_called()
