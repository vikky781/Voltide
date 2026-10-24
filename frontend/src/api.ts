import type { Issue } from './types';

export class ApiError extends Error {
  constructor(message: string, public issues: Issue[] = [], public requestId?: string) { super(message); }
}

export async function api<T>(path: string, body?: FormData): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { method: body ? 'POST' : 'GET', body, credentials: 'same-origin' });
  } catch { throw new ApiError('Cannot reach the server. Check your connection and try again.'); }
  let data;
  try { data = await response.json(); }
  catch { throw new ApiError('The server could not complete this request. Please try again later.'); }
  if (!response.ok) throw new ApiError(data.error || 'Request failed.', data.errors || [], data.request_id);
  return data as T;
}

export function forecastForm(file: File, windowStart?: string, settings?: object): FormData {
  const body = new FormData();
  body.set('file', file);
  if (windowStart) body.set('window_start', windowStart);
  if (settings) body.set('battery_settings', JSON.stringify(settings));
  return body;
}
