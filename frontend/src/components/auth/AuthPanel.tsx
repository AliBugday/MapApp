"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api";
import { useUser } from "@/lib/auth";

/**
 * One form for both signing in and registering.
 *
 * The two flows differ only in which endpoint they hit, so a single form with a toggle
 * is less code and less UI than two panels.
 */
export default function AuthPanel() {
  const { signIn, signUp } = useUser();
  const [mode, setMode] = useState<"signin" | "register">("signin");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const registering = mode === "register";

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const action = registering ? signUp : signIn;
      await action(username.trim(), password);
      setPassword("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Bir şeyler ters gitti. Tekrar deneyin.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h2 style={{ fontSize: "0.95rem", marginTop: 0 }}>
        {registering ? "Hesap oluştur" : "Giriş yap"}
      </h2>
      <p style={{ color: "var(--muted)", fontSize: "0.78rem", marginTop: 0 }}>
        Sorun bildirmek için bir hesabınızın olması gerekir.
      </p>

      <label style={{ display: "block", marginBottom: "0.5rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Kullanıcı adı</span>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
      </label>

      <label style={{ display: "block", marginBottom: "0.75rem" }}>
        <span style={{ fontSize: "0.8rem" }}>Şifre</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={registering ? "new-password" : "current-password"}
          required
        />
      </label>

      {error && (
        <p
          role="alert"
          style={{
            background: "#fdecea",
            border: "1px solid #f5c2bd",
            borderRadius: 4,
            padding: "0.5rem",
            fontSize: "0.8rem",
            marginTop: 0,
          }}
        >
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting || !username.trim() || !password}
        style={{
          background: "var(--accent)",
          color: "white",
          border: 0,
          borderRadius: 4,
          padding: "0.5rem 0.9rem",
          width: "100%",
        }}
      >
        {submitting ? "İşleniyor…" : registering ? "Hesap oluştur" : "Giriş yap"}
      </button>

      <p style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
        {registering ? "Zaten bir hesabınız var mı?" : "Hesabınız yok mu?"}{" "}
        <button
          type="button"
          onClick={() => {
            setMode(registering ? "signin" : "register");
            setError(null);
          }}
          style={{
            background: "none",
            border: 0,
            padding: 0,
            color: "var(--accent)",
            textDecoration: "underline",
          }}
        >
          {registering ? "Giriş yap" : "Kayıt ol"}
        </button>
      </p>
    </form>
  );
}
