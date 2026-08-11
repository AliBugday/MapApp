import AppHeader from "@/components/AppHeader";
import MapPanel from "@/components/map/MapPanel";

export default function HomePage() {
  return (
    <main style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <AppHeader />
      <MapPanel />
    </main>
  );
}
