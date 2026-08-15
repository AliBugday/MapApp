"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { fetchNotifications, markNotificationsRead, type Notification } from "@/lib/api";
import { useUser } from "@/lib/auth";
import { TYPE_LABELS } from "@/lib/typeLabels";

// Polling, not websockets: CLAUDE.md rules out Redis/extra infra, and this is
// indistinguishable from real-time in a demo.
const POLL_INTERVAL_MS = 20_000;

export default function NotificationBell() {
  const { user } = useUser();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);

  const refresh = useCallback(() => {
    // A failed poll just tries again next interval — not worth surfacing to the user.
    fetchNotifications()
      .then(setNotifications)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!user) return;
    refresh();
    const id = setInterval(refresh, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [user, refresh]);

  if (!user) return null;

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  async function handleToggle() {
    const next = !open;
    setOpen(next);
    if (next && unreadCount > 0) {
      try {
        await markNotificationsRead();
        setNotifications((current) => current.map((n) => ({ ...n, is_read: true })));
      } catch {
        // Leave the badge as-is; the next poll will retry the mark-as-read implicitly
        // by the user reopening the dropdown.
      }
    }
  }

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => void handleToggle()}
        aria-label="Bildirimler"
        style={{
          position: "relative",
          background: "transparent",
          border: "1px solid var(--border)",
          borderRadius: 4,
          padding: "0.25rem 0.6rem",
          fontSize: "0.9rem",
          cursor: "pointer",
        }}
      >
        🔔
        {unreadCount > 0 && (
          <span
            style={{
              position: "absolute",
              top: -4,
              right: -4,
              background: "#b3261e",
              color: "white",
              borderRadius: 999,
              fontSize: "0.65rem",
              padding: "0.05rem 0.35rem",
              lineHeight: 1.3,
            }}
          >
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            right: 0,
            marginTop: "0.3rem",
            background: "white",
            border: "1px solid var(--border)",
            borderRadius: 6,
            padding: "0.6rem 0.75rem",
            boxShadow: "0 1px 4px rgba(0,0,0,0.2)",
            minWidth: 240,
            maxHeight: 320,
            overflowY: "auto",
            zIndex: 1000,
          }}
        >
          {notifications.length === 0 ? (
            <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: 0 }}>
              Henüz bildirim yok.
            </p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {notifications.map((notification) => (
                <li
                  key={notification.id}
                  style={{
                    padding: "0.35rem 0",
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <Link
                    href={`/reports/${notification.report_id}`}
                    style={{ fontSize: "0.85rem" }}
                    onClick={() => setOpen(false)}
                  >
                    {notification.report_title}
                  </Link>
                  <div style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
                    Yakınınızda: {TYPE_LABELS[notification.report_type]} ·{" "}
                    {new Date(notification.created_at).toLocaleDateString("tr-TR")}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
