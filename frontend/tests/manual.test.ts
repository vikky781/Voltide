import { describe, expect, it } from 'vitest';
import { manualRows } from '../src/manual';

describe('dataset-local manual hours', () => {
  it('creates 24 blank weather rows across year rollover without inventing readings', () => {
    const rows = manualRows('2026-12-31T18:00');
    expect(rows).toHaveLength(24);
    expect(rows[0]).toEqual({ timestamp: '2026-12-31 18:00:00', ambient_temp_c: '', humidity_pct: '', solar_irradiance_wm2: '' });
    expect(rows[23].timestamp).toBe('2027-01-01 17:00:00');
  });
  it('keeps every wall-clock hour across a daylight-saving transition date', () => {
    const rows = manualRows('2026-03-08T00:00');
    expect(rows[2].timestamp).toBe('2026-03-08 02:00:00');
    expect(rows[23].timestamp).toBe('2026-03-08 23:00:00');
    expect(new Set(rows.map(row => row.timestamp)).size).toBe(24);
  });
  it('rejects invalid dates, non-hourly starts, and incomplete input', () => {
    for (const invalid of ['', '2026-02-30T00:00', '2026-01-01T12:15', 'bad', '2026-01-01']) {
      expect(manualRows(invalid)).toEqual([]);
    }
  });
});
