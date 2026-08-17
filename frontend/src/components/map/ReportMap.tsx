"use client";

import { MapContainer, Marker, Popup, TileLayer, Tooltip, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

import Image from "next/image";
import Link from "next/link";

import UpvoteButton from "@/components/UpvoteButton";
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
}: ReportMapProps) {
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

      {reports.map((report) => {
        const isPastEvent =
          report.type === "event" &&
          report.event_ends_at != null &&
          new Date(report.event_ends_at) < new Date();

        return (
          <Marker
            key={report.id}
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
                  {report.organization_parent_name ? ` · ${report.organization_parent_name}` : ""}
                </div>
              )}
              <div>
                ▲ {report.upvote_count} · 💬 {report.comment_count}
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
              <strong>{report.title}</strong>
              {report.description && <p style={{ margin: "0.25rem 0" }}>{report.description}</p>}
              <small>
                {TYPE_LABELS[report.type]} · {STATUS_LABELS[report.status]}
                {report.author_username ? ` · bildiren: ${report.author_username}` : ""}
              </small>
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
