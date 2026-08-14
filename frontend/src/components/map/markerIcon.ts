import L from "leaflet";

import type { Report } from "@/lib/api";
import { TYPE_COLORS, TYPE_GLYPHS } from "@/lib/typeLabels";

export interface PinInput {
  type: Report["type"];
  status: Report["status"];
  visibility: Report["visibility"];
  upvote_count: number;
  comment_count: number;
  /** First uploaded photo, once image upload exists. Falls back to the type glyph. */
  thumbnailUrl?: string | null;
}

const RESOLVED_RING = "#9aa4b2";

function sizeFor(engagement: number): number {
  if (engagement >= 10) return 46;
  if (engagement >= 3) return 36;
  return 28;
}

function keyFor(pin: PinInput): string {
  return [
    pin.type,
    pin.status,
    pin.visibility,
    pin.upvote_count,
    pin.comment_count,
    pin.thumbnailUrl ?? "",
  ].join("|");
}

// Building a fresh L.divIcon on every render makes Leaflet tear down and rebuild marker
// DOM each time, which visibly flickers — icons are cached by their visual inputs instead.
const cache = new Map<string, L.DivIcon>();

export function iconFor(pin: PinInput): L.DivIcon {
  const key = keyFor(pin);
  const cached = cache.get(key);
  if (cached) return cached;

  const isResolved = (pin.type === "issue" || pin.type === "request") && pin.status === "resolved";
  const isPrivate =
    (pin.type === "announcement" || pin.type === "event") && pin.visibility === "members";

  const size = sizeFor(pin.upvote_count + pin.comment_count);
  const ringColor = isResolved ? RESOLVED_RING : TYPE_COLORS[pin.type];

  // The centre only ever shows a photo (our own /media/ URL, generated server-side) or a
  // fixed glyph string from TYPE_GLYPHS — never report title/author text — so this string
  // carries no injectable user input.
  const centerHtml = pin.thumbnailUrl
    ? `<img src="${pin.thumbnailUrl}" alt="" class="pin-photo" />`
    : `<span class="pin-glyph">${TYPE_GLYPHS[pin.type]}</span>`;

  const badgeHtml =
    pin.upvote_count > 0 ? `<span class="pin-badge">${pin.upvote_count}</span>` : "";

  const cornerHtml = isResolved
    ? `<span class="pin-corner" title="Çözüldü">✓</span>`
    : isPrivate
      ? `<span class="pin-corner" title="Yalnızca üyelere">🔒</span>`
      : "";

  const html = `
    <div class="pin-wrap">
      <div class="pin${isResolved ? " pin-resolved" : ""}" style="border-color:${ringColor}">
        ${centerHtml}
      </div>
      ${badgeHtml}
      ${cornerHtml}
    </div>
  `;

  const icon = L.divIcon({
    html,
    className: "pin-icon",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
  cache.set(key, icon);
  return icon;
}
