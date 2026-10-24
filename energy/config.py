"""India-region settings for the verified Voltide QuickML endpoint."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re

from dotenv import load_dotenv

from energy.features import FEATURE_VERSION


@dataclass(frozen=True)
class QuickMLSettings:
    endpoint_url: str
    model_version: str
    org_id: str
    project_id: str
    endpoint_key: str = field(repr=False)
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)
    refresh_token: str = field(repr=False)
    environment: str = 'Development'
    accounts_url: str = 'https://accounts.zoho.in'
    feature_version: str = FEATURE_VERSION

    def __post_init__(self):
        if not all(isinstance(value, str) and value.strip() for value in vars(self).values()):
            raise ValueError('Missing required QuickML settings.')
        if not re.fullmatch(r'\d+', self.project_id) or not re.fullmatch(r'\d+', self.org_id):
            raise ValueError('Invalid Catalyst project or organization identifier.')
        expected = f'https://api.catalyst.zoho.in/quickml/v1/project/{self.project_id}/endpoints/predict'
        if self.endpoint_url != expected or self.accounts_url != 'https://accounts.zoho.in':
            raise ValueError('QuickML credentials require the configured India-region Zoho destinations.')
        if self.environment not in {'Development', 'Production'}:
            raise ValueError('Unsupported Catalyst environment.')
        if self.feature_version != FEATURE_VERSION:
            raise ValueError('QuickML feature version differs from the application feature contract.')

    @classmethod
    def from_env(cls, env=None):
        if env is None:
            load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)
            env = os.environ
        fields = {'endpoint_url': 'QUICKML_ENDPOINT_URL', 'endpoint_key': 'QUICKML_ENDPOINT_KEY',
                  'model_version': 'QUICKML_MODEL_VERSION', 'org_id': 'CATALYST_ORG_ID',
                  'project_id': 'CATALYST_PROJECT_ID', 'client_id': 'ZOHO_CLIENT_ID',
                  'client_secret': 'ZOHO_CLIENT_SECRET', 'refresh_token': 'ZOHO_REFRESH_TOKEN'}
        missing = [name for name in fields.values() if not env.get(name)]
        if missing:
            raise ValueError('Missing required QuickML settings: ' + ', '.join(missing))
        return cls(**{key: env[name] for key, name in fields.items()},
                   environment=env.get('CATALYST_ENVIRONMENT', 'Development'),
                   accounts_url=env.get('ZOHO_ACCOUNTS_URL', 'https://accounts.zoho.in'),
                   feature_version=env.get('QUICKML_FEATURE_VERSION', FEATURE_VERSION))
