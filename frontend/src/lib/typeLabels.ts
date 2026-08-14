import type { Report } from "./api";

/**
 * Shared by the map pin, the legend, the sidebar list and the report form, so a type only
 * needs defining in one place. The stored value stays English — it's an API contract —
 * only what a person sees is Turkish.
 */
export const TYPE_LABELS: Record<Report["type"], string> = {
  issue: "Sorun / Şikayet",
  request: "Talep",
  announcement: "Duyuru",
  event: "Etkinlik",
};

/** Pin ring colour, keyed by type. */
export const TYPE_COLORS: Record<Report["type"], string> = {
  issue: "#e5484d",
  request: "#1f6feb",
  announcement: "#8e4ec6",
  event: "#30a46c",
};

/** Pin centre glyph, used when a report has no photo. */
export const TYPE_GLYPHS: Record<Report["type"], string> = {
  issue: "🛠️",
  request: "🙋",
  announcement: "📣",
  event: "🎉",
};

/** Only announcement/event can be organization-only content — see ReportSerializer.validate(). */
export const ORG_ONLY_TYPES: ReadonlySet<Report["type"]> = new Set(["announcement", "event"]);
