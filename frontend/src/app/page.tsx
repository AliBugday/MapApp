import MapPanel from "@/components/map/MapPanel";

export default function HomePage() {
  return (
    <main style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
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
          Click the map to report an issue. Sign in at{" "}
          <a href="/admin/" style={{ color: "var(--accent)" }}>
            /admin
          </a>{" "}
          first.
        </span>
      </header>
      <MapPanel />
    </main>
  );
}
