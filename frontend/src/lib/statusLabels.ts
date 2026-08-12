import type { Report } from "./api";

/**
 * Shared by the map popup, the sidebar list and the detail page, so a status only needs
 * translating in one place. The stored value (the Report["status"] key) stays in English —
 * it's an API contract — only the label shown to a person is Turkish.
 */
export const STATUS_LABELS: Record<Report["status"], string> = {
  open: "Açık",
  in_progress: "İşlemde",
  resolved: "Çözüldü",
  rejected: "Reddedildi",
};
