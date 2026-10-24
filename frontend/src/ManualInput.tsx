import type { ManualRow } from './manual';

const fields = [ ['ambient_temp_c', 'Temperature °C'], ['humidity_pct', 'Humidity %'],
  ['solar_irradiance_wm2', 'Irradiance W/m²'] ] as const;

export default function ManualInput({ rows, disabled, validated, onChange, onValidate }: {
  rows: ManualRow[]; disabled: boolean; validated: boolean; onChange: (rows: ManualRow[]) => void; onValidate: () => void;
}) {
  if (!rows.length) return null;
  return <details className="panel manual-input" open={!validated}>
    <summary>Hourly weather entry · {validated ? 'Checked — expand to edit' : '24 readings required'}</summary>
    <p className="muted">Enter measured weather for each hour. A blank value can only be carried from the immediately preceding original hourly reading; the first hour must be complete.</p>
    <div className="table-scroll" tabIndex={0} aria-label="Manual telemetry entry"><table><thead><tr><th scope="col">Hour</th>{fields.map(([key, label]) => <th scope="col" key={key}>{label}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={row.timestamp}><th scope="row">{row.timestamp}</th>{fields.map(([key, label]) => <td key={key}><input type="number" step="any" aria-label={`${label}, row ${index + 1}, ${row.timestamp}`} disabled={disabled} value={row[key]} onChange={event => onChange(rows.map((item, at) => at === index ? { ...item, [key]: event.target.value } : item))} /></td>)}</tr>)}</tbody></table></div>
    <button className="secondary" disabled={disabled} onClick={onValidate}>Check 24 hours</button>
  </details>;
}
