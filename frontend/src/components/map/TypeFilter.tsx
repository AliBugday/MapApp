"use client";

import { useEffect, useRef, useState } from "react";

import type { Report } from "@/lib/api";
import { TYPE_COLORS, TYPE_LABELS } from "@/lib/typeLabels";

interface TypeFilterProps {
  allTypes: Array<Report["type"]>;
  activeTypes: Set<Report["type"]>;
  onToggleType: (type: Report["type"]) => void;
}

/** Multi-select combobox for the sidebar's type filter — a single compact control instead
 * of a row/column of always-visible toggles, so the report list keeps most of the space. */
export default function TypeFilter({ allTypes, activeTypes, onToggleType }: TypeFilterProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (event: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const summary =
    activeTypes.size === allTypes.length
      ? "Filter"
      : allTypes
          .filter((type) => activeTypes.has(type))
          .map((type) => TYPE_LABELS[type])
          .join(", ");

  return (
    <div ref={rootRef} style={{ position: "relative", marginBottom: "0.75rem" }}>
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        aria-haspopup="listbox"
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "0.4rem",
          padding: "0.4rem 0.6rem",
          border: "1px solid var(--border)",
          borderRadius: 4,
          background: "#fff",
          fontSize: "0.85rem",
          textAlign: "left",
        }}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {summary}
        </span>
        <span aria-hidden style={{ color: "var(--muted)", flexShrink: 0 }}>
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open && (
        <div
          role="listbox"
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            right: 0,
            zIndex: 20,
            background: "#fff",
            border: "1px solid var(--border)",
            borderRadius: 4,
            padding: "0.35rem 0.5rem",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.12)",
          }}
        >
          {allTypes.map((type) => (
            <label
              key={type}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.4rem",
                fontSize: "0.85rem",
                padding: "0.3rem 0",
              }}
            >
              <input
                type="checkbox"
                checked={activeTypes.has(type)}
                onChange={() => onToggleType(type)}
                style={{ width: "auto", accentColor: TYPE_COLORS[type] }}
              />
              <span>{TYPE_LABELS[type]}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
