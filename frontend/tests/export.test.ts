import { expect, it } from 'vitest';
import { forecastCSV } from '../src/export';
import type { Forecast } from '../src/types';

const fixture = { hourly: [{ timestamp: '2015-01-01 18:00:00', target_demand_kw: 200.00001,
  requested_mode: 'RENEWABLE_STORAGE', reasons: ['DEMAND_THRESHOLD', 'PEAK_WINDOW'], critical_overload: true,
  battery_soc_start_pct: 20, battery_soc_end_pct: 20, battery_delivered_kw: 0, unserved_kw: 200.00001,
  storage_shortfall: true, alerts: ['CRITICAL_OVERLOAD', 'STORAGE_SHORTFALL'] }] } as Forecast;

it('exports full prediction precision and exact timestamp text for unsaved runs', () => {
  expect(forecastCSV(fixture, 'predictions')).toBe('timestamp,target_demand_kw\r\n2015-01-01 18:00:00,200.00001\r\n');
});
it('exports dispatch, battery, reasons, and both independent alert codes', () => {
  const csv = forecastCSV(fixture, 'dispatch');
  expect(csv).toContain('battery_soc_end_pct');
  expect(csv).toContain('DEMAND_THRESHOLD|PEAK_WINDOW');
  expect(csv).toContain('CRITICAL_OVERLOAD|STORAGE_SHORTFALL');
  expect(csv.trim().split('\r\n')).toHaveLength(2);
});
