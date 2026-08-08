import type { Report } from "@/lib/api";

export interface LatLng {
  latitude: number;
  longitude: number;
}

/**
 * The only contract between the app and the mapping library.
 *
 * Everything Leaflet-specific lives inside this directory, so swapping to
 * MapLibre later means reimplementing ReportMap and nothing else.
 */
export interface ReportMapProps {
  reports: Report[];
  pending: LatLng | null;
  onMapClick: (position: LatLng) => void;
  center: LatLng;
  zoom: number;
}
