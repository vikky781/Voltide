export type ManualRow = { timestamp: string; ambient_temp_c: string; humidity_pct: string; solar_irradiance_wm2: string };

// UTC calendar arithmetic preserves naive dataset hours, including DST transition dates.
// These timestamps are never converted to the browser's timezone.
export function manualRows(start: string): ManualRow[] {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):00$/.exec(start);
  if (!match) return [];
  const [year, month, day, hour] = match.slice(1).map(Number);
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  date.setUTCHours(hour, 0, 0, 0);
  if (year < 1 || date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day || date.getUTCHours() !== hour) return [];
  return Array.from({ length: 24 }, (_, index) => {
    const at = new Date(date.getTime() + index * 3600000);
    return { timestamp: at.toISOString().slice(0, 19).replace('T', ' '),
      ambient_temp_c: '', humidity_pct: '', solar_irradiance_wm2: '' };
  });
}
