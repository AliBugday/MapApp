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
    event_starts_at?: string;
    event_ends_at?: string;
    images: File[];
  }) => Promise<void>;
  onCancel: () => void;
}

const TYPES = Object.keys(TYPE_LABELS) as Array<Report["type"]>;

/** "YYYY-MM-DDTHH:mm" in local time, the format a datetime-local input's value/min needs. */
function toDatetimeLocal(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function NewReportForm({ position, onSubmit, onCancel }: Props) {
  const { user } = useUser();
  const canPostOrgOnly = Boolean(user?.organization_name);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState<Report["type"]>("issue");
  const [visibility, setVisibility] = useState<Report["visibility"]>("public");
  const [eventStartsAt, setEventStartsAt] = useState("");
  const [eventEndsAt, setEventEndsAt] = useState("");
  const [images, setImages] = useState<File[]>([]);
  // <input type="file"> is uncontrolled and, more importantly, replaces its FileList on
  // every dialog open rather than adding to it — reopening the picker to add a second
  // photo would otherwise wipe out the first. Bumping this key remounts the input after
  // every pick (not just on submit), so `images` in state is the only accumulator and the
  // native element never carries a stale selection forward.
  const [fileInputKey, setFileInputKey] = useState(0);
  const [saving, setSaving] = useState(false);

  const showVisibility = ORG_ONLY_TYPES.has(type);
  const showEventTimes = type === "event";

  function handleFilesSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(event.target.files ?? []);
    setImages((current) => [...current, ...picked]);
    setFileInputKey((key) => key + 1);
  }

  function removeImage(index: number) {
    setImages((current) => current.filter((_, i) => i !== index));
  }

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
        event_starts_at: showEventTimes ? new Date(eventStartsAt).toISOString() : undefined,
        event_ends_at: showEventTimes ? new Date(eventEndsAt).toISOString() : undefined,
        images,
      });
      setTitle("");
      setDescription("");
      setType("issue");
      setVisibility("public");
      setEventStartsAt("");
      setEventEndsAt("");
      setImages([]);
      setFileInputKey((key) => key + 1);
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

      {showEventTimes && (
        <>
          <label style={{ display: "block", marginBottom: "0.5rem" }}>
            <span style={{ fontSize: "0.8rem" }}>Başlangıç zamanı</span>
            <input
              type="datetime-local"
              value={eventStartsAt}
              min={toDatetimeLocal(new Date())}
              required
              onChange={(e) => setEventStartsAt(e.target.value)}
            />
          </label>
          <label style={{ display: "block", marginBottom: "0.75rem" }}>
            <span style={{ fontSize: "0.8rem" }}>Bitiş zamanı</span>
            <input
              type="datetime-local"
              value={eventEndsAt}
              min={eventStartsAt || toDatetimeLocal(new Date())}
              required
              onChange={(e) => setEventEndsAt(e.target.value)}
            />
          </label>
        </>
      )}

      <label style={{ display: "block", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Fotoğraflar (isteğe bağlı)</span>
        <input
          key={fileInputKey}
          type="file"
          accept="image/*"
          multiple
          onChange={handleFilesSelected}
        />
      </label>

      {images.length > 0 && (
        <ul
          style={{
            listStyle: "none",
            padding: 0,
            margin: "0 0 0.75rem",
            fontSize: "0.8rem",
            display: "flex",
            flexDirection: "column",
            gap: "0.2rem",
          }}
        >
          {images.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}
            >
              <span
                style={{
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  flex: 1,
                }}
              >
                {file.name}
              </span>
              <button
                type="button"
                onClick={() => removeImage(index)}
                aria-label={`${file.name} kaldır`}
                style={{
                  background: "transparent",
                  border: 0,
                  color: "var(--muted)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
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
