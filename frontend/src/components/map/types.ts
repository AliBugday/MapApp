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
  onToggleUpvote: (report: Pick<Report, "id" | "has_upvoted">) => void;
  center: LatLng;
  zoom: number;
  /** The signed-in user's own home/work points, private — never another user's. */
  homeLocation?: LatLng | null;
  workLocation?: LatLng | null;
  /** Fired on mount and on every pan/zoom with the current viewport as
   * "minLng,minLat,maxLng,maxLat" — what the backend's ?bbox= param expects. */
  onBoundsChange: (bbox: string) => void;
  /** Set from the sidebar list (not map interaction) to fly to and open a report's
   * popup — lets a list click show the same on-map preview a pin click would. */
  selectedReportId?: number | null;
}
