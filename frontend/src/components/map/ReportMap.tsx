"use client";

import { useEffect, useRef } from "react";
import { MapContainer, Marker, Popup, TileLayer, Tooltip, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

import Image from "next/image";
import Link from "next/link";

import UpvoteButton from "@/components/UpvoteButton";
import type { Report } from "@/lib/api";
import { formatEventRange } from "@/lib/format";
import { STATUS_LABELS } from "@/lib/statusLabels";
import { TYPE_LABELS } from "@/lib/typeLabels";
import { iconFor } from "./markerIcon";
import type { LatLng, ReportMapProps } from "./types";

// Leaflet resolves its default icons with relative URLs that break under a bundler,
// so the marker images are wired up explicitly from the imported assets.
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x.src,
  iconUrl: markerIcon.src,
  shadowUrl: markerShadow.src,
});

function ClickHandler({ onMapClick }: { onMapClick: (position: LatLng) => void }) {
  useMapEvents({
    click(event) {
      onMapClick({ latitude: event.latlng.lat, longitude: event.latlng.lng });
    },
  });
  return null;
}

// "minLng,minLat,maxLng,maxLat" — exactly what the backend's parse_bbox() expects.
// Padded 20% so a small pan within the current view doesn't immediately reveal an empty
// edge before the next fetch lands.
function boundsToBbox(bounds: L.LatLngBounds): string {
  const padded = bounds.pad(0.2);
  const sw = padded.getSouthWest();
  const ne = padded.getNorthEast();
  return `${sw.lng},${sw.lat},${ne.lng},${ne.lat}`;
}

function BoundsHandler({ onBoundsChange }: { onBoundsChange: (bbox: string) => void }) {
  // In Leaflet a zoom also ends with moveend, so this one listener covers both pan and
  // zoom without double-firing.
  const map = useMapEvents({
    moveend() {
      onBoundsChange(boundsToBbox(map.getBounds()));
    },
  });
  useEffect(() => {
    onBoundsChange(boundsToBbox(map.getBounds()));
    // Only ever the initial view — moveend above covers every change after mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

// Flies to and opens the popup of whichever report the sidebar list last selected. A plain
// prop change rather than map interaction, so this has to reach into the map imperatively
// via refs (react-leaflet has no declarative "open this marker's popup" API).
function FlyToSelected({
  reportId,
  reports,
  markerRefs,
}: {
  reportId: number | null | undefined;
  reports: Report[];
  markerRefs: React.RefObject<Record<number, L.Marker | null>>;
}) {
  const map = useMap();
  useEffect(() => {
    if (reportId == null) return;
    const report = reports.find((r) => r.id === reportId);
    const marker = markerRefs.current[reportId];
    if (!report || !marker) return;
    map.flyTo([report.latitude, report.longitude], Math.max(map.getZoom(), 15));
    marker.openPopup();
    // Only reportId should retrigger this — reports/markerRefs/map are stable identities
    // (or, for `reports`, change on every fetch without the selection itself changing).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId]);
  return null;
}

// Fixed, built once — unlike report pins there are at most two of these and they change
// rarely, so markerIcon.ts's per-render caching machinery would be overkill here.
const HOME_ICON = L.divIcon({
  html: `<span style="font-size:22px">🏠</span>`,
  className: "location-marker-icon",
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});
const WORK_ICON = L.divIcon({
  html: `<span style="font-size:22px">💼</span>`,
  className: "location-marker-icon",
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

export default function ReportMap({
  reports,
  pending,
  onMapClick,
  onToggleUpvote,
  center,
  zoom,
  homeLocation,
  workLocation,
  onBoundsChange,
  selectedReportId,
}: ReportMapProps) {
  const markerRefs = useRef<Record<number, L.Marker | null>>({});

  return (
    <MapContainer
      center={[center.latitude, center.longitude]}
      zoom={zoom}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickHandler onMapClick={onMapClick} />
      <BoundsHandler onBoundsChange={onBoundsChange} />
      <FlyToSelected reportId={selectedReportId} reports={reports} markerRefs={markerRefs} />

      {reports.map((report) => {
        const isPastEvent =
          report.type === "event" &&
          report.event_ends_at != null &&
          new Date(report.event_ends_at) < new Date();

        return (
          <Marker
            key={report.id}
            ref={(instance) => {
              markerRefs.current[report.id] = instance;
            }}
            position={[report.latitude, report.longitude]}
            icon={iconFor({
              type: report.type,
              status: report.status,
              visibility: report.visibility,
              upvote_count: report.upvote_count,
              comment_count: report.comment_count,
              thumbnailUrl: report.images[0]?.thumbnail_url,
              isPastEvent,
              organizationLogoUrl: report.organization_logo_url,
            })}
          >
            <Tooltip direction="top" offset={[0, -6]}>
              <div
                style={{
                  position: "relative",
                  paddingRight: report.organization_logo_url ? "1.6rem" : 0,
                }}
              >
                {report.organization_logo_url && (
                  <Image
                    src={report.organization_logo_url}
                    alt=""
                    width={22}
                    height={22}
                    style={{
                      position: "absolute",
                      top: -4,
                      right: -4,
                      borderRadius: "999px",
                      border: "1.5px solid #d8dce2",
                      background: "#fff",
                      objectFit: "contain",
                    }}
                  />
                )}
                <strong>{report.title}</strong>
                <div>
                  {TYPE_LABELS[report.type]}
                  {report.type === "issue" || report.type === "request"
                    ? ` · ${STATUS_LABELS[report.status]}`
                    : report.type === "event" && report.event_starts_at && report.event_ends_at
                      ? ` · ${formatEventRange(report.event_starts_at, report.event_ends_at)}`
                      : report.visibility === "members"
                        ? " · Yalnızca üyelere"
                        : ""}
                </div>
                {report.organization_name && (
                  <div>
                    {report.organization_name}
                    {report.organization_parent_name
                      ? ` · ${report.organization_parent_name}`
                      : ""}
                  </div>
                )}
                <div>
                  ▲ {report.upvote_count} · 💬 {report.comment_count}
                </div>
              </div>
              {report.images.length > 0 && (
                // Up to 4 photos: 1–3 lay out in a single row, 4 wraps into a 2×2 grid —
                // both fall out of the same "2 columns once there are 4" grid rule.
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${Math.min(report.images.length, 4) === 4 ? 2 : Math.min(report.images.length, 4)}, auto)`,
                    gap: "0.2rem",
                    marginTop: "0.3rem",
                  }}
                >
                  {report.images.slice(0, 4).map((image) => (
                    <Image
                      key={image.id}
                      src={image.thumbnail_url}
                      alt=""
                      width={96}
                      height={96}
                      style={{ objectFit: "cover", borderRadius: 4 }}
                    />
                  ))}
                </div>
              )}
            </Tooltip>
            <Popup>
              <div
                style={{
                  position: "relative",
                  paddingRight: report.organization_logo_url ? "1.6rem" : 0,
                }}
              >
                {report.organization_logo_url && (
                  <Image
                    src={report.organization_logo_url}
                    alt=""
                    width={22}
                    height={22}
                    style={{
                      position: "absolute",
                      top: -4,
                      right: -4,
                      borderRadius: "999px",
                      border: "1.5px solid #d8dce2",
                      background: "#fff",
                      objectFit: "contain",
                    }}
                  />
                )}
                <strong>{report.title}</strong>
                {report.description && (
                  <p style={{ margin: "0.25rem 0" }}>{report.description}</p>
                )}
                <small>
                  {TYPE_LABELS[report.type]} · {STATUS_LABELS[report.status]}
                  {report.author_username ? ` · bildiren: ${report.author_username}` : ""}
                </small>
              </div>
              <div
                style={{
                  marginTop: "0.5rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.75rem",
                }}
              >
                {report.type !== "event" && (
                  <UpvoteButton report={report} onToggle={onToggleUpvote} />
                )}
                <Link href={`/reports/${report.id}`}>Detaylar ve yorumlar</Link>
              </div>
            </Popup>
          </Marker>
        );
      })}

      {pending && (
        <Marker position={[pending.latitude, pending.longitude]} opacity={0.6}>
          <Popup>Buraya yeni bildirim</Popup>
        </Marker>
      )}

      {homeLocation && (
        <Marker position={[homeLocation.latitude, homeLocation.longitude]} icon={HOME_ICON}>
          <Tooltip direction="top" offset={[0, -6]}>
            Ev konumunuz
          </Tooltip>
        </Marker>
      )}
      {workLocation && (
        <Marker position={[workLocation.latitude, workLocation.longitude]} icon={WORK_ICON}>
          <Tooltip direction="top" offset={[0, -6]}>
            İş/okul konumunuz
          </Tooltip>
        </Marker>
      )}
    </MapContainer>
  );
}
