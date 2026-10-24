import { useEffect, useState } from 'react';
import { api, ApiError } from './api';
import type { Forecast } from './types';

type SavedRun = { run_id: string; first_timestamp: string; created_at: string; peak_demand_kw: number; critical_count: number; model_version: string };

export default function RunHistory({ revision, disabled, onLoad, onBusy }: { revision?: string; disabled: boolean; onLoad: (run: Forecast) => void; onBusy: (value: boolean) => void }) {
  const [runs, setRuns] = useState<SavedRun[]>([]);
  const [refresh, setRefresh] = useState(0);
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    setLoading(true); setError('');
    api<{ runs: SavedRun[] }>('/api/runs').then(data => { if (active) setRuns(data.runs); })
      .catch(error => { if (active) setError(error instanceof ApiError ? error.message : 'History is unavailable.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [revision, refresh]);
  async function open(id: string) {
    setOpening(true); onBusy(true); setError('');
    try { onLoad(await api<Forecast>(`/api/runs/${encodeURIComponent(id)}`)); }
    catch (error) { setError(error instanceof ApiError ? error.message : 'Unable to open saved run.'); }
    finally { setOpening(false); onBusy(false); }
  }
  return <section className="panel history" aria-label="Saved forecast history">
    <div className="panel-title"><h2>Saved runs</h2><button className="secondary" disabled={loading || opening || disabled} onClick={() => setRefresh(value => value + 1)}>Refresh</button></div>
    <p className="muted">Latest 20 runs from this browser session. Clearing cookies removes access.</p>
    {error && <p className="notice" role="alert">{error}</p>}
    {loading ? <p role="status">Loading history…</p> : !error && !runs.length ? <p className="muted">Your saved forecasts will appear here.</p> : null}
    {runs.length > 0 && <ul className="history-list">{runs.map(run => <li key={run.run_id}><button disabled={disabled || opening || loading} onClick={() => void open(run.run_id)}><strong>{run.first_timestamp}</strong><span>{run.peak_demand_kw.toFixed(1)} kW peak · {run.critical_count} critical hours</span><small>{run.model_version} · Saved {run.created_at}</small></button></li>)}</ul>}
  </section>;
}
