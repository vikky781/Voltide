import type { Forecast, Hour } from './types';

export function forecastCSV(run: Forecast, kind: 'predictions' | 'dispatch'): string {
  const columns: (keyof Hour)[] = kind === 'predictions' ? ['timestamp', 'target_demand_kw'] : [
    'timestamp', 'target_demand_kw', 'requested_mode', 'reasons', 'critical_overload',
    'battery_soc_start_pct', 'battery_soc_end_pct', 'battery_delivered_kw', 'unserved_kw',
    'storage_shortfall', 'alerts'];
  const cell = (value: Hour[keyof Hour]) => {
    const text = Array.isArray(value) ? value.join('|') : String(value);
    return /[",\r\n]/.test(text) ? '"' + text.replaceAll('"', '""') + '"' : text;
  };
  return [columns.join(','), ...run.hourly.map(row => columns.map(key => cell(row[key])).join(','))].join('\r\n') + '\r\n';
}

export function downloadForecast(run: Forecast, kind: 'predictions' | 'dispatch') {
  const url = URL.createObjectURL(new Blob([forecastCSV(run, kind)], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url; link.download = `voltide-${run.run_id}-${kind}.csv`;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
