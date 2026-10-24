export type Issue = { row: number; column: string; message: string; code?: string };
export type Weather = { timestamp: string; ambient_temp_c: number; humidity_pct: number; solar_irradiance_wm2: number };
export type Correction = { row: number; column: string; previous_row: number; value: number; reason: string };
export type Preview = { rows: Weather[]; window_starts: string[]; warnings: string[]; corrections: Correction[] };
export type BatterySettings = {
  capacity_kwh: number; initial_soc_pct: number; reserve_soc_pct: number;
  max_discharge_kw: number; discharge_efficiency_pct: number;
};
export type Hour = {
  timestamp: string; target_demand_kw: number; requested_mode: 'MAIN_GRID' | 'RENEWABLE_STORAGE';
  reasons: string[]; critical_overload: boolean; battery_soc_start_pct: number;
  battery_soc_end_pct: number; battery_delivered_kw: number; unserved_kw: number;
  storage_shortfall: boolean; alerts: string[];
};
export type Forecast = {
  run_id: string; model_version: string; feature_version: string; generated_at: string;
  saved: boolean; warnings: string[]; battery_provenance: 'SIMULATED'; battery_settings: BatterySettings;
  corrections: Correction[]; hourly: Hour[];
  summary: { peak_demand_kw: number; total_energy_kwh: number; storage_hours: number;
    critical_hours: number; final_soc_pct: number; unserved_energy_kwh: number };
};
