import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export default function SubdivisionMap({
  geojson,
}: {
  geojson: GeoJSON.Geometry | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current || !geojson) return;

    if (mapRef.current) {
      mapRef.current.remove();
    }

    const map = L.map(containerRef.current, {
      scrollWheelZoom: false,
      attributionControl: false,
    });
    mapRef.current = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(map);

    const layer = L.geoJSON(geojson as GeoJSON.GeoJsonObject, {
      style: {
        color: "#3b82f6",
        weight: 2,
        fillColor: "#3b82f6",
        fillOpacity: 0.15,
      },
    }).addTo(map);

    map.fitBounds(layer.getBounds(), { padding: [20, 20] });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [geojson]);

  if (!geojson) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        No geometry data available
      </div>
    );
  }

  return <div ref={containerRef} className="w-full h-full min-h-[300px] rounded-lg" />;
}
