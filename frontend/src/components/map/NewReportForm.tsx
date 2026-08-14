"use client";

import { useState } from "react";

import type { Report } from "@/lib/api";
import { ORG_ONLY_TYPES, TYPE_LABELS } from "@/lib/typeLabels";
import { useUser } from "@/lib/auth";
import type { LatLng } from "./types";

interface Props {
  position: LatLng;
  onSubmit: (input: {
    title: string;
    description: string;
    type: Report["type"];
    visibility?: Report["visibility"];
  }) => Promise<void>;
  onCancel: () => void;
}

const TYPES = Object.keys(TYPE_LABELS) as Array<Report["type"]>;

export default function NewReportForm({ position, onSubmit, onCancel }: Props) {
  const { user } = useUser();
  const canPostOrgOnly = Boolean(user?.organization_name);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState<Report["type"]>("issue");
  const [visibility, setVisibility] = useState<Report["visibility"]>("public");
  const [saving, setSaving] = useState(false);

  const showVisibility = ORG_ONLY_TYPES.has(type);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim(),
        type,
        visibility: showVisibility ? visibility : undefined,
      });
      setTitle("");
      setDescription("");
      setType("issue");
      setVisibility("public");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2 style={{ fontSize: "0.95rem", marginTop: 0 }}>Yeni bildirim</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.78rem", marginTop: 0 }}>
        {position.latitude.toFixed(5)}, {position.longitude.toFixed(5)}
      </p>

      <label style={{ display: "block", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Başlık</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} />
      </label>

      <label style={{ display: "block", marginBottom: "0.75rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Açıklama</span>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
      </label>

      <label style={{ display: "block", marginBottom: "0.75rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Tür</span>
        <select value={type} onChange={(e) => setType(e.target.value as Report["type"])}>
          {TYPES.map((t) => (
            <option key={t} value={t} disabled={ORG_ONLY_TYPES.has(t) && !canPostOrgOnly}>
              {TYPE_LABELS[t]}
              {ORG_ONLY_TYPES.has(t) && !canPostOrgOnly ? " (yalnızca kurum hesapları)" : ""}
            </option>
          ))}
        </select>
      </label>

      {showVisibility && (
        <fieldset
          style={{ border: "1px solid var(--border)", borderRadius: 4, marginBottom: "0.75rem" }}
        >
          <legend style={{ fontSize: "0.8rem", padding: "0 0.3rem" }}>Görünürlük</legend>
          <label style={{ display: "block", fontSize: "0.85rem", marginBottom: "0.25rem" }}>
            <input
              type="radio"
              name="visibility"
              checked={visibility === "public"}
              onChange={() => setVisibility("public")}
              style={{ width: "auto", marginRight: "0.4rem" }}
            />
            Herkese açık
          </label>
          <label style={{ display: "block", fontSize: "0.85rem" }}>
            <input
              type="radio"
              name="visibility"
              checked={visibility === "members"}
              onChange={() => setVisibility("members")}
              style={{ width: "auto", marginRight: "0.4rem" }}
            />
            Yalnızca üyelere
          </label>
        </fieldset>
      )}

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
          {saving ? "Kaydediliyor…" : "Kaydet"}
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
          İptal
        </button>
      </div>
    </form>
  );
}
