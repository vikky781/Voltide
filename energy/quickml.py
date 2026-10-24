"""Real QuickML inference only: ordered batches, refresh auth, bounded failures."""

import math
from numbers import Real
from threading import Lock
import time

import requests

from energy.config import QuickMLSettings
from energy.contracts import PredictionError


class QuickMLClient:
    BATCH_SIZE = 24  # Verified with the live endpoint; larger sizes are not assumed.

    def __init__(self, settings: QuickMLSettings, *, transport=None,
                 clock=time.monotonic, sleep=time.sleep):
        self.settings = settings
        self.model_version = settings.model_version
        self.transport = transport if transport is not None else requests.Session()
        self.clock, self.sleep = clock, sleep
        self._token, self._expires = None, 0
        self._token_lock = Lock()

    def _remaining(self, deadline):
        remaining = deadline - self.clock()
        if remaining <= 0:
            raise PredictionError('QuickML request deadline exceeded.')
        return remaining

    def _access_token(self, deadline, *, invalidate=None):
        with self._token_lock:
            if invalidate is not None and self._token == invalidate:
                self._token = None
            remaining = self._remaining(deadline)
            if self._token and self.clock() < self._expires:
                return self._token
            s = self.settings
            try:
                response = self.transport.post(s.accounts_url + '/oauth/v2/token', data={
                    'grant_type': 'refresh_token', 'refresh_token': s.refresh_token,
                    'client_id': s.client_id, 'client_secret': s.client_secret,
                }, timeout=min(15, remaining), allow_redirects=False)
                body = response.json()
                token = body.get('access_token') if isinstance(body, dict) else None
                expiry = body.get('expires_in', 3600) if isinstance(body, dict) else 0
                if (response.status_code != 200 or not isinstance(token, str) or not token
                        or isinstance(expiry, bool) or not isinstance(expiry, Real)
                        or not math.isfinite(expiry) or expiry <= 60):
                    raise ValueError('Invalid token response')
            except (requests.RequestException, ValueError):
                raise PredictionError('QuickML authorization failed. Check private OAuth settings.') from None
            self._token, self._expires = token, self.clock() + expiry - 60
            return token

    def _chunk(self, rows, deadline):
        token = self._access_token(deadline)
        refreshed = False
        retries = 0
        while True:
            remaining = self._remaining(deadline)
            try:
                response = self.transport.post(self.settings.endpoint_url, json={'data': rows},
                    headers={'Authorization': 'Zoho-oauthtoken ' + token,
                             'X-QUICKML-ENDPOINT-KEY': self.settings.endpoint_key,
                             'CATALYST-ORG': self.settings.org_id,
                             'Environment': self.settings.environment},
                    timeout=min(20, remaining), allow_redirects=False)
            except (requests.Timeout, requests.ConnectionError):
                response = None
            except requests.RequestException:
                raise PredictionError('QuickML transport failed.') from None
            if response is not None and response.status_code == 401 and not refreshed:
                token = self._access_token(deadline, invalidate=token)
                refreshed = True
                continue
            transient = response is None or response.status_code in {429, 500, 502, 503, 504}
            if transient and retries < 2:
                delay = float(2 ** retries)
                if response is not None and response.status_code == 429:
                    try:
                        delay = max(delay, float(response.headers.get('Retry-After', delay)))
                    except (TypeError, ValueError):
                        raise PredictionError('QuickML rate limit reached; retry later.') from None
                if not math.isfinite(delay) or delay > 5 or delay >= self._remaining(deadline):
                    raise PredictionError('QuickML rate limit or request deadline reached.')
                self.sleep(delay)
                retries += 1
                continue
            if response is None or response.status_code != 200:
                raise PredictionError('QuickML inference failed; no predictions were substituted.')
            try:
                body = response.json()
            except ValueError:
                raise PredictionError('QuickML returned malformed JSON.') from None
            values = body.get('result') if isinstance(body, dict) else None
            if (not isinstance(values, list) or len(values) != len(rows)
                    or body.get('status', 'success') != 'success'
                    or any(isinstance(value, bool) or not isinstance(value, Real)
                           or not math.isfinite(value) or value < 0 for value in values)):
                raise PredictionError('QuickML returned invalid or misaligned demand predictions.')
            return [float(value) for value in values]

    def predict_rows(self, features: list[dict]) -> list[float]:
        if not features:
            raise PredictionError('QuickML requires at least one feature row.')
        deadline = self.clock() + 120
        predictions = []
        for start in range(0, len(features), self.BATCH_SIZE):
            predictions.extend(self._chunk(features[start:start + self.BATCH_SIZE], deadline))
        self._remaining(deadline)
        return predictions
