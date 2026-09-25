import type { AssetRow, Value } from "./api";

export type RiskLevel = "high" | "medium" | "low" | "unknown";

export const mid = (v: Value | undefined | null): number | null => {
  if (v === null || v === undefined) return null;
  if (typeof v === "number") return v;
  if ("unknown" in v) return null;
  return (v.low + v.high) / 2;
};

/** Screening label derived from computed depth above floor. Illustrative thresholds, shown as such. */
export function riskLevel(a: AssetRow): RiskLevel {
  const d = mid(a.depth_above_floor_m);
  if (d === null) return "unknown";
  if (d >= 0.5) return "high";
  if (d >= 0.1) return "medium";
  return "low";
}

export const sectorClass = (sector: string): string =>
  /manufact/i.test(sector) ? "p-factory" : /transport|storage/i.test(sector) ? "p-warehouse" : /wholesale|distrib/i.test(sector) ? "p-dist" : "p-cold";

export const assetClass = (type: string): string =>
  type === "industrial_building" ? "p-factory" : type === "warehouse" ? "p-warehouse" : type === "distribution_centre" ? "p-dist" : "p-cold";

export function greetingKey(): "good_morning" | "good_afternoon" | "good_evening" {
  const h = new Date().getHours();
  return h < 12 ? "good_morning" : h < 18 ? "good_afternoon" : "good_evening";
}
