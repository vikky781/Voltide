import { lazy, Suspense, useEffect, useState } from 'react';
import { manualRows, type ManualRow } from './manual';
import ManualInput from './ManualInput';
import RunHistory from './RunHistory';
import { downloadForecast } from './export';
import { api, ApiError, forecastForm } from './api';
import type { BatterySettings, Forecast, Preview } from './types';

const DemandChart = lazy(() => import('./DemandChart'));
const defaults: BatterySettings = { capacity_kwh: 2000, initial_soc_pct: 80, reserve_soc_pct: 20,
  max_discharge_kw: 250, discharge_efficiency_pct: 95 };
const hour = (timestamp: string) => timestamp.slice(11, 16);
const number = (value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 1 });
const reasonLabels: Record<string, string> = { DEMAND_THRESHOLD: 'Demand > 160 kW', PEAK_WINDOW: 'Peak window', NORMAL_LOAD: 'Normal load' };

export default function App() {
  const [health, setHealth] = useState<'checking' | 'ready' | 'unavailable'>('checking');
  const [source, setSource] = useState<'csv' | 'manual'>('csv');
  const [manualStart, setManualStart] = useState('');
  const [manual, setManual] = useState<ManualRow[]>([]);
  const [resultState, setResultState] = useState<'current' | 'previous' | 'saved'>('current');
  const [historyRevision, setHistoryRevision] = useState('');
  const [file, setFile] = useState<File>();
  const [preview, setPreview] = useState<Preview>();
  const [start, setStart] = useState('');
  const [settings, setSettings] = useState(defaults);
  const [run, setRun] = useState<Forecast>();
  const [busy, setBusy] = useState<'validate' | 'forecast' | 'history' | null>(null);
  const [error, setError] = useState<ApiError>();
  useEffect(() => {
    let active = true;
    api<{ model_configured: boolean }>('/api/health').then(data => {
      if (active) setHealth(data.model_configured ? 'ready' : 'unavailable');
    }).catch(() => { if (active) setHealth('unavailable'); });
    return () => { active = false; };
  }, []);

  async function validate(selected?: File) {
    setFile(selected); setPreview(undefined); setResultState('previous'); setError(undefined); setStart('');
    if (!selected) return;
    if (selected.size > 2 * 1024 * 1024) { setError(new ApiError('Choose a CSV smaller than 2 MiB.')); return; }
    setBusy('validate');
    try {
      const data = await api<Preview>('/api/validate', forecastForm(selected));
      setPreview(data); setStart(data.window_starts[0] || '');
    } catch (error) { setError(error instanceof ApiError ? error : new ApiError('Unable to validate CSV.')); }
    finally { setBusy(null); }
  }

  function inputsChanged() { setPreview(undefined); setStart(''); setError(undefined); setResultState('previous'); }

  async function validateManual() {
    inputsChanged(); setBusy('validate');
    try {
      const data = await api<Preview>('/api/validate', { source_rows: manual });
      setPreview(data); setStart(data.window_starts[0] || '');
    } catch (error) { setError(error instanceof ApiError ? error : new ApiError('Unable to validate telemetry.')); }
    finally { setBusy(null); }
  }

  async function forecast() {
    if (!start || (source === 'csv' ? !file : manual.length !== 24)) return;
    setBusy('forecast'); setError(undefined); setResultState('previous');
    try {
      const data = await api<Forecast>('/api/forecast', source === 'csv' ? forecastForm(file!, start, settings) : { source_rows: manual, window_start: start, battery_settings: settings });
      setRun(data); setResultState('current');
      if (data.saved) setHistoryRevision(data.run_id);
    }
    catch (error) { setError(error instanceof ApiError ? error : new ApiError('Unable to calculate forecast.')); }
    finally { setBusy(null); }
  }

  const visibleRows = preview?.rows.filter(row => row.timestamp.trim() >= start).slice(0, 24) || [];
  return <>
    <a className="skip" href="#workspace">Skip to forecast</a>
    <header className="topbar">
      <a className="brand" href="#workspace" aria-label="Voltide home"><svg viewBox="0 0 32 32" aria-hidden="true"><path d="M3 7h7l5 17h4L27 7M6 16h20" /></svg>voltide<span>Microgrid intelligence</span></a>
      <div className={`service-status ${health}`}><span aria-hidden="true" />{health === 'ready' ? 'Forecast service configured' : health === 'checking' ? 'Checking service' : 'Forecast service unavailable'}</div>
    </header>
    <main id="workspace">
      <div className="page-heading"><div><p className="eyebrow">Demand & dispatch</p><h1>See the next 24 hours.</h1><p>Forecast demand. Plan the switch. Understand the battery limits.</p></div><span className="environment">Planning workspace</span></div>
      <div className="workspace-grid">
        <aside className="input-panel" aria-label="Forecast inputs">
          <div className="panel-title"><h2>Weather input</h2><span className="unit">24 hourly readings</span></div>
          <div className="source-tabs" role="group" aria-label="Telemetry source">{(['csv', 'manual'] as const).map(mode => <button key={mode} aria-pressed={source === mode} disabled={!!busy} onClick={() => { setSource(mode); inputsChanged(); }}>{mode === 'csv' ? 'Upload CSV' : 'Enter manually'}</button>)}</div>
          <p className="muted">Use weather telemetry to forecast a consecutive day.</p>
          {source === 'csv' ? <>
          <label className="upload" htmlFor="csv"><span className="upload-symbol" aria-hidden="true">↥</span><strong>{file?.name || 'Choose a telemetry CSV'}</strong><span>CSV · up to 2 MiB / 10,000 rows</span><input id="csv" type="file" accept=".csv,text/csv" disabled={!!busy} onChange={event => void validate(event.target.files?.[0])} /></label>
          <details className="format-help"><summary>Required CSV columns</summary><code>timestamp<br />ambient_temp_c<br />humidity_pct<br />solar_irradiance_wm2</code><p>Timestamp format: 2015-01-01 00:00:00. Values use the dataset’s local clock.</p></details>
          </> : <><label className="field" htmlFor="manual-start">First hour (dataset local clock)<input id="manual-start" type="datetime-local" step="3600" disabled={!!busy} value={manualStart} onChange={event => { setManualStart(event.target.value); setManual(manualRows(event.target.value)); inputsChanged(); }} /></label><p className="muted">Choose the first hour, then enter 24 readings in the table. Changing the first hour clears those readings.</p>{manualStart && !manual.length && <p className="notice">Choose a valid date and an exact hour.</p>}</>}
          {preview && <div className="validation-status"><strong>{preview.rows.length.toLocaleString()} valid rows</strong><span>{preview.window_starts.length.toLocaleString()} available 24-hour windows</span></div>}
          <label className="field" htmlFor="window">Forecast starts at<select id="window" value={start} disabled={!preview?.window_starts.length || !!busy} onChange={event => { setStart(event.target.value); setResultState('previous'); }}><option value="">{preview ? 'Choose a valid window' : 'Validate telemetry first'}</option>{preview?.window_starts.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
          {preview && !preview.window_starts.length && <p className="notice">No consecutive 24-hour window found. Check for duplicate timestamps, gaps, or fewer than 24 rows.</p>}
          <details className="battery-settings"><summary>Battery assumptions <span className="simulated">Simulated</span></summary><p className="muted">No battery measurements are present. This simulation allows discharge only; no charging is assumed.</p><fieldset disabled={!!busy}><legend className="sr-only">Battery settings</legend>
            {([
              ['capacity_kwh', 'Capacity (kWh)', 0.1, undefined, 1],
              ['initial_soc_pct', 'Initial charge (%)', 0, 100, 1],
              ['reserve_soc_pct', 'Reserve (%)', 0, 100, 1],
              ['max_discharge_kw', 'Max discharge (kW)', 0.1, undefined, 1],
              ['discharge_efficiency_pct', 'Discharge efficiency (%)', 0.1, 100, 0.1],
            ] as const).map(([key, label, min, max, step]) => <label className="field compact" key={key}>{label}<input type="number" min={min} max={max} step={step} value={Number.isNaN(settings[key]) ? '' : settings[key]} onChange={event => { setSettings({ ...settings, [key]: event.target.valueAsNumber }); setResultState('previous'); }} /></label>)}
          </fieldset></details>
          <button className="primary" disabled={!start || (source === 'csv' ? !file : manual.length !== 24) || !!busy || health !== 'ready' || Object.values(settings).some(value => !Number.isFinite(value))} onClick={() => void forecast()}>{busy === 'forecast' ? 'Forecasting with QuickML…' : busy === 'validate' ? 'Checking your CSV…' : 'Generate forecast'}<span aria-hidden="true">↗</span></button>
          <p className="footnote">Rules are fixed: storage above 160 kW or 18:00–22:00. Critical alert at 200 kW.</p>
        </aside>
        <section className="results" aria-label="Forecast results" aria-busy={busy === 'forecast'}>
          <div role="status" className="sr-only">{busy === 'validate' ? 'Validating telemetry' : busy === 'forecast' ? 'Forecast in progress' : run ? 'Forecast complete' : ''}</div>
          {source === 'manual' && <ManualInput rows={manual} disabled={!!busy} validated={!!preview} onChange={rows => { setManual(rows); inputsChanged(); }} onValidate={() => void validateManual()} />}
          {run && resultState !== 'current' && <p className="notice" role="status">{resultState === 'saved' ? 'Viewing a saved run. The input editor is separate from this result.' : 'Previous successful forecast. Current inputs have not produced a new result.'}</p>}
          {error && <div className="error" role="alert"><h2>Request could not be completed</h2><p>{error.message}</p>{error.issues.length > 0 && <ul>{error.issues.slice(0, 20).map((issue, index) => <li key={index}>Row {issue.row} · {issue.column}: {issue.message}</li>)}</ul>}{error.issues.length > 20 && <p>{error.issues.length - 20} more issues. Correct the telemetry and validate again.</p>}{error.requestId && <small>Request {error.requestId}</small>}</div>}
          {!run ? <>
            <div className="empty-forecast"><div className="empty-glyph" aria-hidden="true"><span /><span /><span /><span /><span /><span /><span /></div><p className="eyebrow">Your operating horizon</p><h2>{busy === 'forecast' ? 'Building your forecast…' : preview ? 'Weather checked. Ready to forecast.' : 'A clearer picture starts with your data.'}</h2><p>{busy === 'forecast' ? 'Retrieving real cloud predictions and applying the dispatch rules.' : preview ? 'Choose a 24-hour window and review the battery assumptions, then generate your forecast.' : 'Upload a CSV or enter hourly weather to reveal demand, energy source decisions, and potential battery shortfalls.'}</p><div className="empty-key"><span>Weather telemetry</span><b aria-hidden="true">→</b><span>Demand forecast</span><b aria-hidden="true">→</b><span>Hourly dispatch</span></div></div>
            {visibleRows.length > 0 && <section className="panel"><div className="panel-title"><h2>Selected weather window</h2><span className="unit">{visibleRows.length} hours</span></div><WeatherPreview preview={preview!} start={start} /></section>}
          </> : <ForecastResults run={run} />}
          {preview && preview.corrections.length > 0 && <details className="panel correction"><summary>{preview.corrections.length} weather correction(s) applied</summary><p>Missing values were carried from the immediately preceding original hourly reading.</p><ul>{preview.corrections.map((item, index) => <li key={index}>Row {item.row}, {item.column}: {item.value}, from row {item.previous_row}.</li>)}</ul></details>}
          <RunHistory revision={historyRevision} disabled={!!busy} onBusy={value => setBusy(value ? 'history' : null)} onLoad={saved => { setRun(saved); setResultState('saved'); setError(undefined); }} />
          {preview?.warnings.map((warning, index) => <p className="notice" key={index}>{warning}</p>)}
        </section>
      </div>
      <footer>Voltide <span>Forecasts inform planning. Battery behavior is simulated. No physical switches are controlled.</span></footer>
    </main>
  </>;
}

function WeatherPreview({ preview, start }: { preview: Preview; start: string }) {
  const rows = [...preview.rows].sort((a, b) => a.timestamp.localeCompare(b.timestamp)).filter(row => row.timestamp.trim() >= start).slice(0, 24);
  return <div className="table-scroll" tabIndex={0} aria-label="Weather preview table"><table><thead><tr><th scope="col">Time</th><th scope="col">Temp °C</th><th scope="col">Humidity %</th><th scope="col">Irradiance W/m²</th></tr></thead><tbody>{rows.map(row => <tr key={row.timestamp}><th scope="row">{row.timestamp}</th><td>{row.ambient_temp_c}</td><td>{row.humidity_pct}</td><td>{row.solar_irradiance_wm2}</td></tr>)}</tbody></table></div>;
}

function ForecastResults({ run }: { run: Forecast }) {
  const summary = run.summary;
  return <>
    <div className="run-heading"><div><p className="eyebrow">24-hour forecast</p><h2>{run.hourly[0].timestamp.slice(0, 10)} <span>from {hour(run.hourly[0].timestamp)}</span></h2></div><span className="simulated">Battery simulated</span></div>
    <div className="export-actions"><button className="secondary" onClick={() => downloadForecast(run, 'predictions')}>Download predictions CSV</button><button className="secondary" onClick={() => downloadForecast(run, 'dispatch')}>Download dispatch CSV</button></div>
    <div className="metrics"><div><span>Peak demand</span><strong>{number(summary.peak_demand_kw)}<small>kW</small></strong></div><div><span>Total demand</span><strong>{number(summary.total_energy_kwh)}<small>kWh</small></strong></div><div><span>Storage requested</span><strong>{summary.storage_hours}<small>hours</small></strong></div><div className={summary.critical_hours ? 'critical-metric' : ''}><span>Critical hours</span><strong>{summary.critical_hours}<small>≥ 200 kW</small></strong></div></div>
    {summary.critical_hours > 0 && <p className="error" role="alert">Critical overload predicted in {summary.critical_hours} hour(s): demand reaches or exceeds 200 kW. Review the flagged hourly decisions.</p>}
    <section className="panel chart-panel"><div className="panel-title"><h2>Demand outlook</h2><span className="unit">kW · hourly</span></div><Suspense fallback={<div className="chart" role="status">Loading demand chart…</div>}><DemandChart run={run} /></Suspense><div className="legend"><span><i className="demand-key" />Predicted demand</span><span>– – Storage above 160 kW</span><span className="critical-text">– – Critical at 200 kW</span></div></section>
    <section className="panel"><div className="panel-title"><h2>Dispatch horizon</h2><span className="unit">Requested energy source</span></div><div className="dispatch-tape">{run.hourly.map(row => <div key={row.timestamp} className={row.requested_mode === 'MAIN_GRID' ? 'grid' : 'storage'} title={`${row.timestamp}: ${row.requested_mode.replaceAll('_', ' ')}, ${number(row.target_demand_kw)} kW`}><span>{hour(row.timestamp).slice(0, 2)}</span><i aria-hidden="true" />{row.critical_overload && <b aria-label="Critical overload">!</b>}</div>)}</div><div className="legend"><span><i className="grid-key" />Main grid</span><span><i className="storage-key" />Renewable/storage</span><span className="critical-text">! Critical overload</span></div></section>
    <section className="battery-result"><div><p className="eyebrow">Battery simulation</p><h2>{number(summary.final_soc_pct)}% <span>charge remaining</span></h2><p>Reserve {run.battery_settings.reserve_soc_pct}% · Capacity {number(run.battery_settings.capacity_kwh)} kWh · Initial {run.battery_settings.initial_soc_pct}% · Max discharge {number(run.battery_settings.max_discharge_kw)} kW · Efficiency {run.battery_settings.discharge_efficiency_pct}% · No charging</p></div><div><span>Unserved storage request</span><strong>{number(summary.unserved_energy_kwh)} <small>kWh</small></strong></div></section>
    {summary.unserved_energy_kwh > 0 && <p className="notice">Storage shortfall: the simulated battery cannot cover every requested hour. The requested dispatch mode is preserved; unserved demand is shown below.</p>}
    {run.warnings.map((warning, index) => <p className="notice" key={index}>{warning}</p>)}
    <section className="panel"><div className="panel-title"><h2>Hourly decisions</h2><span className="unit">Full precision used for rules</span></div><div className="table-scroll" tabIndex={0} aria-label="Hourly dispatch table"><table><thead><tr><th scope="col">Time</th><th scope="col">Demand kW</th><th scope="col">Requested source / reason</th><th scope="col">Battery kW</th><th scope="col">Unserved kW</th><th scope="col">End charge %</th><th scope="col">Alerts</th></tr></thead><tbody>{run.hourly.map(row => <tr key={row.timestamp}><th scope="row">{row.timestamp}</th><td className={row.critical_overload ? 'critical-text' : ''}>{number(row.target_demand_kw)}</td><td><span className={`mode ${row.requested_mode === 'MAIN_GRID' ? 'grid' : 'storage'}`}>{row.requested_mode === 'MAIN_GRID' ? 'Main grid' : 'Renewable/storage'}</span><small className="reasons">{row.reasons.map(reason => reasonLabels[reason] || reason).join(' · ')}</small></td><td>{number(row.battery_delivered_kw)}</td><td>{number(row.unserved_kw)}</td><td>{number(row.battery_soc_end_pct)}</td><td className="critical-text">{row.alerts.map(alert => alert === 'CRITICAL_OVERLOAD' ? 'Critical overload' : 'Storage shortfall').join(' · ') || '—'}</td></tr>)}</tbody></table></div></section>
    {run.corrections.length > 0 && <details className="panel correction"><summary>{run.corrections.length} correction(s) in this forecast</summary><ul>{run.corrections.map((item, index) => <li key={index}>Row {item.row}, {item.column}: {item.value}, from row {item.previous_row}.</li>)}</ul></details>}
    <p className="run-meta">Model {run.model_version} · Features {run.feature_version} · {run.saved ? 'Saved to history' : 'Not saved'}<br />Run {run.run_id}</p>
  </>;
}
