"use client";

import { useUser } from "@/lib/auth";

/**
 * Split out of page.tsx as a client component: it is the only part of the page that
 * needs the auth context, so the page itself stays server-rendered.
 */
export default function AppHeader() {
  const { user, loading, signOut } = useUser();

  return (
    <header
      style={{
        padding: "0.75rem 1rem",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "baseline",
        gap: "1rem",
      }}
    >
      <h1 style={{ margin: 0, fontSize: "1.1rem" }}>MapApp</h1>
      <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
        Click the map to report an issue.
      </span>

      <span style={{ marginLeft: "auto", color: "var(--muted)", fontSize: "0.85rem" }}>
        {loading ? (
          "…"
        ) : user ? (
          <>
            Signed in as <strong>{user.username}</strong>{" "}
            <button
              type="button"
              onClick={() => void signOut()}
              style={{
                background: "none",
                border: 0,
                padding: 0,
                marginLeft: "0.35rem",
                color: "var(--accent)",
                textDecoration: "underline",
                font: "inherit",
              }}
            >
              Log out
            </button>
          </>
        ) : (
          "Not signed in"
        )}
      </span>
    </header>
  );
}
