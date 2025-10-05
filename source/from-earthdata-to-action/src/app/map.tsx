/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import "leaflet.heat";
import "leaflet/dist/leaflet.css";

// Fix for default marker icon
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

import { useMap } from "react-leaflet/hooks";
import { useEffect, useMemo, useRef, useState } from "react";

function HeatLayer({
  addressPoints,
}: {
  addressPoints: [number, number, number][];
}) {
  const map = useMap();

  useEffect(() => {
    // Check if heatLayer is available
    if (typeof (L as any).heatLayer === "undefined") {
      console.error("Leaflet.heat plugin not loaded properly");
      return;
    }

    const points: L.HeatLatLngTuple[] = addressPoints.map((p) => [
      p[0],
      p[1],
      p[2],
    ]);

    // Create heat layer with options
    const heat = (L as any)
      .heatLayer(points, {
        radius: 25,
        blur: 15,
        maxZoom: 17,
        minOpacity: 0.5,
      })
      .addTo(map);

    // Cleanup function to remove heat layer when component unmounts
    return () => {
      map.removeLayer(heat);
    };
  }, [map, addressPoints]);

  return null;
}

function DraggableMarker({
  initialPosition,
}: {
  initialPosition: [number, number];
}) {
  const [position, setPosition] = useState(initialPosition);
  const markerRef = useRef<L.Marker>(null);

  const eventHandlers = useMemo(
    () => ({
      dragend() {
        const marker = markerRef.current;
        if (marker != null) {
          const newPosition = marker.getLatLng();
          setPosition([newPosition.lat, newPosition.lng]);
        }
      },
    }),
    []
  );

  useEffect(() => {
    console.log("Marker position changed:", position);
  }, [position]);

  return (
    <Marker
      draggable={true}
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
    >
      <Popup>You can drag this marker.</Popup>
    </Marker>
  );
}

function StartView({
  position,
  zoom,
}: {
  position: [number, number];
  zoom: number;
}) {
  const map = useMap();
  useEffect(() => {
    map.setView(position, zoom);
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function Map(props: any) {
  const { position, zoom, showHeatmap, heatMapData } = props;
  return (
    <div className="h-[500px] w-full">
      <MapContainer
        id="map"
        style={{ height: "100%", width: "100%" }}
        center={position}
        zoom={zoom}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <DraggableMarker initialPosition={position} />
        <StartView position={position} zoom={zoom} />
        {showHeatmap && <HeatLayer addressPoints={heatMapData} />}
      </MapContainer>
    </div>
  );
}
