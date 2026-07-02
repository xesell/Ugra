/**
 * Ugra character asset library.
 * Auto-generated from scripts/split_character_assets.py — re-run script after sheet updates.
 */

import manifest from "../../../public/assets/ugra/manifest.json";

export type UgraAssetKey = keyof typeof manifest.assets;
export type UgraEventKey = keyof typeof manifest.eventMap;

export const UGRA_ASSETS = manifest.assets as Record<string, string>;
export const UGRA_EVENT_MAP = manifest.eventMap as Record<string, string>;

/** Resolve asset URL by logical key, e.g. "states/greeting" */
export function ugraAsset(key: UgraAssetKey | string): string {
  return UGRA_ASSETS[key] ?? UGRA_ASSETS["states/greeting"];
}

/** Map domain event / agent state to character pose */
export function ugraPoseForEvent(eventType: string): string {
  return ugraAsset(UGRA_EVENT_MAP[eventType] ?? "states/greeting");
}

/** All agent state poses for picker / documentation */
export const UGRA_STATES = Object.keys(UGRA_ASSETS)
  .filter((k) => k.startsWith("states/"))
  .sort();

export const UGRA_EMOTIONS = Object.keys(UGRA_ASSETS)
  .filter((k) => k.startsWith("emotions/"))
  .sort();

export const UGRA_TURNS = Object.keys(UGRA_ASSETS)
  .filter((k) => k.startsWith("turns/"))
  .sort();

export { manifest as ugraManifest };
