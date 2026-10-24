"""One-time, secret-safe exchange of a user-approved Zoho Self Client grant."""

from getpass import getpass
from pathlib import Path

from dotenv import dotenv_values, set_key
import requests


def exchange_grant(code: str, env_path: Path, transport=requests) -> None:
    settings = dotenv_values(env_path)
    accounts = settings.get('ZOHO_ACCOUNTS_URL', 'https://accounts.zoho.in')
    if accounts != 'https://accounts.zoho.in':
        raise ValueError('This project requires the India Zoho accounts destination.')
    if not code or not settings.get('ZOHO_CLIENT_ID') or not settings.get('ZOHO_CLIENT_SECRET'):
        raise ValueError('A grant code and private client credentials are required.')
    try:
        response = transport.post(accounts + '/oauth/v2/token', data={
            'client_id': settings['ZOHO_CLIENT_ID'],
            'client_secret': settings['ZOHO_CLIENT_SECRET'],
            'grant_type': 'authorization_code', 'code': code,
        }, timeout=30, allow_redirects=False)
        body = response.json()
        token = body.get('refresh_token') if isinstance(body, dict) else None
        if response.status_code != 200 or not isinstance(token, str) or not token:
            raise ValueError('Zoho grant exchange failed; check the scope and code expiry.')
    except (requests.RequestException, ValueError) as error:
        raise ValueError('Zoho grant exchange failed; check the scope and code expiry.') from None
    set_key(env_path, 'ZOHO_REFRESH_TOKEN', token)


if __name__ == '__main__':
    try:
        exchange_grant(getpass('Zoho grant code (hidden): '), Path(__file__).resolve().parents[1] / '.env')
    except ValueError as error:
        raise SystemExit(str(error)) from None
    print('Refresh token saved to ignored .env. No token was printed.')
