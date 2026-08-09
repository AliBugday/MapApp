"use client";

import { useState } from "react";

import type { LatLng } from "./types";

interface Props {
  position: LatLng;
  onSubmit: (input: { title: string; description: string }) => Promise<void>;
  onCancel: () => void;
}

export default function NewReportForm({ position, onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await onSubmit({ title: title.trim(), description: description.trim() });
      setTitle("");
      setDescription("");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2 style={{ fontSize: "0.95rem", marginTop: 0 }}>New report</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.78rem", marginTop: 0 }}>
        {position.latitude.toFixed(5)}, {position.longitude.toFixed(5)}
      </p>

      <label style={{ display: "block", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Title</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} />
      </label>

      <label style={{ display: "block", marginBottom: "0.75rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Description</span>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
      </label>

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <button
          type="submit"
          disabled={saving || !title.trim()}
          style={{
            background: "var(--accent)",
            color: "white",
            border: 0,
            borderRadius: 4,
            padding: "0.5rem 0.9rem",
          }}
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          style={{
            background: "transparent",
            border: "1px solid var(--border)",
            borderRadius: 4,
            padding: "0.5rem 0.9rem",
          }}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
