"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api";
import { useUser } from "@/lib/auth";

/**
 * Split out of page.tsx as a client component: it is the only part of the page that
 * needs the auth context, so the page itself stays server-rendered.
 */
export default function AppHeader() {
  const { user, loading, signOut, armLocationPicking, removeLocation } = useUser();
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuError, setMenuError] = useState<string | null>(null);

  async function handleRemove(kind: "home" | "work") {
    try {
      await removeLocation(kind);
      setMenuError(null);
    } catch (err) {
      setMenuError(err instanceof ApiError ? err.message : "Konum kaldırılamadı.");
    }
  }

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
        Bir sorun bildirmek için haritaya tıklayın.
      </span>

      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.75rem" }}>
        {/* Collapsed by default so the map/sidebar stay uncluttered — this is a profile
            setting, not something needed on every page load. */}
        {user && (
          <div style={{ position: "relative" }}>
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              style={{
                background: "transparent",
                border: "1px solid var(--border)",
                borderRadius: 4,
                padding: "0.25rem 0.6rem",
                fontSize: "0.8rem",
                cursor: "pointer",
              }}
            >
              📍 Konumlarım {menuOpen ? "▴" : "▾"}
            </button>
            {menuOpen && (
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
                  minWidth: 200,
                  zIndex: 1000,
                }}
              >
                {menuError && (
                  <p role="alert" style={{ color: "#b3261e", fontSize: "0.78rem", marginTop: 0 }}>
                    {menuError}
                  </p>
                )}
                {(["home", "work"] as const).map((kind) => {
                  const isSet =
                    kind === "home" ? user.home_latitude != null : user.work_latitude != null;
                  return (
                    <div
                      key={kind}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.4rem",
                        marginBottom: "0.3rem",
                      }}
                    >
                      <span style={{ fontSize: "0.85rem", flex: 1 }}>
                        {kind === "home" ? "🏠 Ev" : "💼 İş/Okul"}
                      </span>
                      <button
                        type="button"
                        onClick={() => {
                          armLocationPicking(kind);
                          setMenuOpen(false);
                        }}
                        style={{
                          background: "transparent",
                          border: "1px solid var(--border)",
                          borderRadius: 4,
                          padding: "0.15rem 0.5rem",
                          fontSize: "0.78rem",
                        }}
                      >
                        {isSet ? "Değiştir" : "Ayarla"}
                      </button>
                      {isSet && (
                        <button
                          type="button"
                          onClick={() => void handleRemove(kind)}
                          style={{
                            background: "transparent",
                            border: "1px solid var(--border)",
                            borderRadius: 4,
                            padding: "0.15rem 0.5rem",
                            fontSize: "0.78rem",
                            color: "#b3261e",
                          }}
                        >
                          Kaldır
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
          {loading ? (
            "…"
          ) : user ? (
            <>
              Giriş yapan: <strong>{user.username}</strong>{" "}
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
                Çıkış yap
              </button>
            </>
          ) : (
            "Giriş yapılmadı"
          )}
        </span>
      </div>
    </header>
  );
}
