import { TYPE_COLORS, TYPE_GLYPHS, TYPE_LABELS } from "@/lib/typeLabels";

const TYPES = Object.keys(TYPE_LABELS) as Array<keyof typeof TYPE_LABELS>;

/**
 * A plain overlay, not a Leaflet control — kept outside <MapContainer> so it never has to
 * fight Leaflet's own pointer/drag handling. Without this, the pin colours are decoration
 * rather than information.
 */
export default function MapLegend() {
  return (
    <div
      style={{
        position: "absolute",
        bottom: 12,
        left: 12,
        zIndex: 1000,
        background: "white",
        border: "1px solid var(--border)",
        borderRadius: 6,
        padding: "0.6rem 0.75rem",
        fontSize: "0.75rem",
        boxShadow: "0 1px 4px rgba(0,0,0,0.2)",
        maxWidth: 220,
      }}
    >
      {TYPES.map((type) => (
        <div
          key={type}
          style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.2rem" }}
        >
          <span
            style={{
              display: "inline-block",
              width: 14,
              height: 14,
              borderRadius: "50%",
              border: `2.5px solid ${TYPE_COLORS[type]}`,
              textAlign: "center",
              lineHeight: "11px",
              fontSize: "8px",
            }}
          >
            {TYPE_GLYPHS[type]}
          </span>
          <span>{TYPE_LABELS[type]}</span>
        </div>
      ))}
      <div style={{ marginTop: "0.35rem", color: "var(--muted)" }}>
        Boyut = ilgi (oy + yorum) · ✓ çözüldü · 🔒 yalnızca üyelere
      </div>
    </div>
  );
}
