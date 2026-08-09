"use client";

import { MapContainer, Marker, Popup, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

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

export default function ReportMap({ reports, pending, onMapClick, center, zoom }: ReportMapProps) {
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
        <Marker key={report.id} position={[report.latitude, report.longitude]}>
          <Popup>
            <strong>{report.title}</strong>
            {report.description && <p style={{ margin: "0.25rem 0" }}>{report.description}</p>}
            <small>
              {report.status} &middot; {report.upvote_count} upvotes
              {report.author_username ? ` · by ${report.author_username}` : ""}
            </small>
          </Popup>
        </Marker>
      ))}

      {pending && (
        <Marker position={[pending.latitude, pending.longitude]} opacity={0.6}>
          <Popup>New report here</Popup>
        </Marker>
      )}
    </MapContainer>
  );
}
