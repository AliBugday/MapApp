"use client";

import { MapContainer, Marker, Popup, TileLayer, Tooltip, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

import Link from "next/link";

import UpvoteButton from "@/components/UpvoteButton";
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

export default function ReportMap({
  reports,
  pending,
  onMapClick,
  onToggleUpvote,
  center,
  zoom,
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

      {reports.map((report) => (
        <Marker
          key={report.id}
          position={[report.latitude, report.longitude]}
          icon={iconFor({
            type: report.type,
            status: report.status,
            visibility: report.visibility,
            upvote_count: report.upvote_count,
            comment_count: report.comment_count,
          })}
        >
          <Tooltip direction="top" offset={[0, -6]}>
            <strong>{report.title}</strong>
            <div>
              {TYPE_LABELS[report.type]}
              {report.type === "issue" || report.type === "request"
                ? ` · ${STATUS_LABELS[report.status]}`
                : report.visibility === "members"
                  ? " · Yalnızca üyelere"
                  : ""}
            </div>
            {report.organization_name && <div>{report.organization_name}</div>}
            <div>
              ▲ {report.upvote_count} · 💬 {report.comment_count}
            </div>
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
              <UpvoteButton report={report} onToggle={onToggleUpvote} />
              <Link href={`/reports/${report.id}`}>Detaylar ve yorumlar</Link>
            </div>
          </Popup>
        </Marker>
      ))}

      {pending && (
        <Marker position={[pending.latitude, pending.longitude]} opacity={0.6}>
          <Popup>Buraya yeni bildirim</Popup>
        </Marker>
      )}
    </MapContainer>
  );
}
