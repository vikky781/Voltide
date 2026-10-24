import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, forecastForm } from '../src/api';

afterEach(() => vi.unstubAllGlobals());

describe('original-source forecast boundary', () => {
  it('resubmits original bytes and explicit window/settings without cleaned preview data', async () => {
    const file = new File(['timestamp,ambient_temp_c\n2015-01-01 00:00:00,\n'], 'weather.csv');
    const form = forecastForm(file, '2015-01-01 01:00:00', { capacity_kwh: 2000 });
    expect(await (form.get('file') as File).text()).toBe(await file.text());
    expect(form.get('window_start')).toBe('2015-01-01 01:00:00');
    expect(JSON.parse(form.get('battery_settings') as string)).toEqual({ capacity_kwh: 2000 });
    expect(form.has('rows')).toBe(false);
  });

  it('retains structured field issues and request id on validation errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      error: 'Invalid weather', errors: [{ row: 2, column: 'humidity_pct', message: 'Out of range' }],
      request_id: 'request-1',
    }), { status: 422 })));
    await expect(api('/api/validate', new FormData())).rejects.toMatchObject({
      message: 'Invalid weather', issues: [{ row: 2, column: 'humidity_pct', message: 'Out of range' }],
      requestId: 'request-1',
    });
  });

  it('reports proxy/non-JSON failure without exposing HTML as application content', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>gateway</html>', { status: 502 })));
    await expect(api('/api/forecast', new FormData())).rejects.toThrow('server');
  });

  it('keeps requests same-origin with browser session cookies', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response('{"status":"ok"}'));
    vi.stubGlobal('fetch', fetch);
    await api('/api/health');
    expect(fetch.mock.calls[0][1]).toMatchObject({ credentials: 'same-origin', method: 'GET' });
  });

  it('submits original manual rows as JSON without substituting cleaned preview values', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response('{"rows":[]}'));
    vi.stubGlobal('fetch', fetch);
    const source = [{ timestamp: '2015-01-01 00:00:00', ambient_temp_c: '' }];
    await api('/api/validate', { source_rows: source });
    expect(JSON.parse(fetch.mock.calls[0][1].body).source_rows).toEqual(source);
    expect(fetch.mock.calls[0][1].headers).toEqual({ 'Content-Type': 'application/json' });
  });
});
