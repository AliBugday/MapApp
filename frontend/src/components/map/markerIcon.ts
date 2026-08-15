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
  /** type="event" whose event_ends_at has passed. Computed by the caller (needs Date.now()),
   * not here, so the cache-key function stays a pure function of its visual inputs. */
  isPastEvent?: boolean;
}

const RESOLVED_RING = "#9aa4b2";

// The classic CSS "map pin" shape: a square with border-radius 50% 50% 50% 0 (three
// rounded corners, one sharp) rotated -45deg turns the sharp corner into a tail pointing
// straight down. That tail sticks out D*(sqrt(2)/2 - 0.5) below the D-diameter round part
// — see the geometry note by TAIL_RATIO below — so the head stays exactly the same size as
// the old plain-circle pins; only a tail is added beneath it.
const TAIL_RATIO = Math.SQRT1_2 - 0.5;

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
    pin.isPastEvent ?? false,
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
  // A pin can't be both resolved (issue/request only) and a past event (event only), so
  // there's no collision to design around — same reasoning as the ✓/🔒 corner-mark slot.
  const isMuted = isResolved || pin.isPastEvent === true;

  const head = sizeFor(pin.upvote_count + pin.comment_count);
  const tail = Math.round(head * TAIL_RATIO);
  const height = head + tail;
  const ringColor = isMuted ? RESOLVED_RING : TYPE_COLORS[pin.type];

  // The centre only ever shows a photo (our own /media/ URL, generated server-side) or a
  // fixed glyph string from TYPE_GLYPHS — never report title/author text — so this string
  // carries no injectable user input. A photo covers the whole rotated shape (head + tail,
  // via .pin-drop-inner's counter-rotation), so it visually continues into the tail; the
  // glyph is a small centred emoji that never stretches, so it only ever reads as sitting
  // in the head — no special-casing needed for that difference.
  const centerHtml = pin.thumbnailUrl
    ? `<img src="${pin.thumbnailUrl}" alt="" class="pin-photo" />`
    : `<span class="pin-glyph">${TYPE_GLYPHS[pin.type]}</span>`;

  const badgeHtml =
    pin.upvote_count > 0 ? `<span class="pin-badge">${pin.upvote_count}</span>` : "";

  // Positioned with `top`, not `bottom`: the wrapper is now taller than the head (it
  // includes the tail), so `bottom` would anchor near the tail tip instead of the head.
  const cornerTop = head - 13;
  const cornerHtml = isResolved
    ? `<span class="pin-corner" style="top:${cornerTop}px" title="Çözüldü">✓</span>`
    : isPrivate
      ? `<span class="pin-corner" style="top:${cornerTop}px" title="Yalnızca üyelere">🔒</span>`
      : "";

  const html = `
    <div class="pin-wrap">
      <div class="pin-drop${isMuted ? " pin-resolved" : ""}"
           style="width:${head}px;height:${head}px;border-color:${ringColor}">
        <div class="pin-drop-inner">${centerHtml}</div>
      </div>
      ${badgeHtml}
      ${cornerHtml}
    </div>
  `;

  // Anchored at the tail's tip (bottom centre), not the head's centre, so the pin actually
  // points at the report's exact coordinate instead of just sitting on top of it.
  const icon = L.divIcon({
    html,
    className: "pin-icon",
    iconSize: [head, height],
    iconAnchor: [head / 2, height],
  });
  cache.set(key, icon);
  return icon;
}
