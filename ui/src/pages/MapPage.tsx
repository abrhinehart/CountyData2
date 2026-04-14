import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import {
  getSubdivisionGeoJSON,
  getCounties,
  getParcelsBySubdivision,
  getSalesBySubdivision,
  getCommissionRoster,
  getInventoryBuilders,
  getPermitDashboard,
} from "../api";
import { getBuilderColor } from "../config/builderColors";
import type {
  SubdivisionGeoFeature,
  ParcelPage,
  PaginatedResponse,
  Transaction,
  CommissionRosterDetail,
  BuilderOut,
  PermitDashboard,
} from "../types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtNum(n: number | null | undefined): string {
  if (n == null) return "";
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function fmtDollar(n: number | null | undefined): string {
  if (n == null) return "";
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

// ---------------------------------------------------------------------------
// SVG stripe pattern for multi-builder polygons
// ---------------------------------------------------------------------------

let patternCounter = 0;

interface BuilderStripeInfo {
  builder_id: number;
  lot_count: number;
}

/**
 * Creates a diagonal stripe SVG pattern in the Leaflet SVG renderer's <defs>.
 * Each stripe width is proportional to the builder's lot share.
 * Returns `url(#patternId)` for use as a fill value.
 */
function getOrCreateStripePattern(
  map: L.Map,
  builders: BuilderStripeInfo[],
): string {
  // Access the SVG renderer's root <svg> element
  const renderer = (map as unknown as { _renderer?: { _container?: SVGSVGElement } })._renderer;
  if (!renderer?._container) return getBuilderColor(builders[0]?.builder_id ?? 0).fill;

  const svg = renderer._container;

  // Ensure <defs> exists
  let defs = svg.querySelector("defs");
  if (!defs) {
    defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    svg.insertBefore(defs, svg.firstChild);
  }

  const totalLots = builders.reduce((sum, b) => sum + b.lot_count, 0);
  if (totalLots === 0) return getBuilderColor(builders[0]?.builder_id ?? 0).fill;

  const patternId = `builder-stripe-${patternCounter++}`;
  const stripeWidth = 12; // total pattern width in px

  const pattern = document.createElementNS("http://www.w3.org/2000/svg", "pattern");
  pattern.setAttribute("id", patternId);
  pattern.setAttribute("patternUnits", "userSpaceOnUse");
  pattern.setAttribute("width", String(stripeWidth));
  pattern.setAttribute("height", String(stripeWidth));
  pattern.setAttribute("patternTransform", "rotate(45)");

  let offset = 0;
  for (const b of builders) {
    const w = (b.lot_count / totalLots) * stripeWidth;
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", String(offset));
    rect.setAttribute("y", "0");
    rect.setAttribute("width", String(w));
    rect.setAttribute("height", String(stripeWidth));
    rect.setAttribute("fill", getBuilderColor(b.builder_id).fill);
    pattern.appendChild(rect);
    offset += w;
  }

  defs.appendChild(pattern);
  return `url(#${patternId})`;
}

/**
 * Remove all builder stripe patterns from the SVG renderer and reset counter.
 */
function clearStripePatterns(map: L.Map) {
  patternCounter = 0;
  const renderer = (map as unknown as { _renderer?: { _container?: SVGSVGElement } })._renderer;
  if (!renderer?._container) return;
  const defs = renderer._container.querySelector("defs");
  if (defs) defs.innerHTML = "";
}

// ---------------------------------------------------------------------------
// Detail panel (shown on polygon click)
// ---------------------------------------------------------------------------

function DetailPanel({
  feature,
  onClose,
}: {
  feature: SubdivisionGeoFeature;
  onClose: () => void;
}) {
  const parcelsQ = useQuery<ParcelPage>({
    queryKey: ["map-parcels", feature.id],
    queryFn: () => getParcelsBySubdivision(feature.id),
  });

  const salesQ = useQuery<PaginatedResponse<Transaction>>({
    queryKey: ["map-sales", feature.name],
    queryFn: () => getSalesBySubdivision(feature.name),
  });

  const commissionQ = useQuery<CommissionRosterDetail>({
    queryKey: ["map-commission", feature.id],
    queryFn: () => getCommissionRoster(feature.id),
  });

  // Builder lots grouped by entity with avg appraised value
  const builderStats = useMemo(() => {
    const items = parcelsQ.data?.items ?? [];
    const map = new Map<string, { count: number; totalValue: number; valueCount: number }>();
    for (const p of items) {
      const name = p.entity ?? p.owner_name ?? "Unknown";
      const entry = map.get(name) ?? { count: 0, totalValue: 0, valueCount: 0 };
      entry.count += 1;
      if (p.appraised_value != null) {
        entry.totalValue += p.appraised_value;
        entry.valueCount += 1;
      }
      map.set(name, entry);
    }
    return [...map.entries()]
      .sort((a, b) => b[1].count - a[1].count)
      .map(([name, s]) => ({
        name,
        count: s.count,
        avgValue: s.valueCount > 0 ? s.totalValue / s.valueCount : null,
      }));
  }, [parcelsQ.data]);

  // Monthly sales velocity
  const monthlyVelocity = useMemo(() => {
    const items = salesQ.data?.items ?? [];
    const map = new Map<string, number>();
    for (const t of items) {
      if (!t.Date) continue;
      const ym = t.Date.slice(0, 7); // YYYY-MM
      map.set(ym, (map.get(ym) ?? 0) + 1);
    }
    return [...map.entries()].sort((a, b) => b[0].localeCompare(a[0]));
  }, [salesQ.data]);

  const actions = commissionQ.data?.actions ?? [];

  return (
    <div className="fixed right-0 top-[53px] bottom-0 w-96 bg-white shadow-xl border-l border-gray-200 z-[1000] overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-start justify-between">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-gray-900 truncate">{feature.name}</h2>
          <p className="text-sm text-gray-500">{feature.county_name}</p>
        </div>
        <button
          onClick={onClose}
          className="ml-2 p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 shrink-0"
          aria-label="Close panel"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-4 space-y-5">
        {/* Builder lots + appraised values */}
        <Section title="Builder Lots">
          {parcelsQ.isLoading ? (
            <p className="text-gray-400 text-sm">Loading...</p>
          ) : parcelsQ.error ? (
            <p className="text-red-500 text-sm">Failed to load parcels</p>
          ) : builderStats.length === 0 ? (
            <p className="text-gray-400 text-sm">No parcels tracked</p>
          ) : (
            <div className="space-y-1.5">
              {builderStats.slice(0, 12).map((b) => (
                <div key={b.name} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 truncate mr-2" title={b.name}>
                    {b.name}
                  </span>
                  <span className="text-gray-500 tabular-nums shrink-0">
                    {fmtNum(b.count)}
                    {b.avgValue != null && (
                      <span className="text-gray-400 ml-1">avg {fmtDollar(b.avgValue)}</span>
                    )}
                  </span>
                </div>
              ))}
              {builderStats.length > 12 && (
                <p className="text-xs text-gray-400">+{builderStats.length - 12} more</p>
              )}
            </div>
          )}
        </Section>

        {/* Monthly sales velocity */}
        <Section title="Sales Velocity">
          {salesQ.isLoading ? (
            <p className="text-gray-400 text-sm">Loading...</p>
          ) : salesQ.error ? (
            <p className="text-red-500 text-sm">Failed to load sales</p>
          ) : monthlyVelocity.length === 0 ? (
            <p className="text-gray-400 text-sm">No sales recorded</p>
          ) : (
            <div className="space-y-1">
              {monthlyVelocity.slice(0, 12).map(([month, count]) => (
                <div key={month} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{month}</span>
                  <span className="text-gray-500 tabular-nums">{count}</span>
                </div>
              ))}
              {monthlyVelocity.length > 12 && (
                <p className="text-xs text-gray-400">+{monthlyVelocity.length - 12} more months</p>
              )}
            </div>
          )}
        </Section>

        {/* Commission actions */}
        {actions.length > 0 && (
          <Section title="Commission Actions">
            <div className="space-y-1.5">
              {actions.slice(0, 6).map((a) => (
                <div key={a.id} className="text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 text-xs shrink-0">{a.meeting_date}</span>
                    <span className="text-gray-700 truncate">
                      {a.approval_type.replace(/_/g, " ")}
                    </span>
                  </div>
                  {a.outcome && (
                    <span
                      className={`text-xs font-medium ${
                        a.outcome === "approved"
                          ? "text-green-600"
                          : a.outcome === "denied"
                            ? "text-red-600"
                            : "text-gray-500"
                      }`}
                    >
                      {a.outcome}
                    </span>
                  )}
                </div>
              ))}
              {actions.length > 6 && (
                <p className="text-xs text-gray-400">+{actions.length - 6} more</p>
              )}
            </div>
          </Section>
        )}

        {/* Link to detail page */}
        <Link
          to={`/subdivisions/${feature.id}`}
          className="block text-center text-sm font-medium text-blue-600 hover:text-blue-800 py-2 border border-blue-200 rounded hover:bg-blue-50 transition-colors"
        >
          View Full Details
        </Link>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">{title}</h3>
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// MapPage
// ---------------------------------------------------------------------------

export default function MapPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const permitLayerRef = useRef<L.LayerGroup | null>(null);
  const svgRendererRef = useRef<L.SVG | null>(null);

  const [selectedCounty, setSelectedCounty] = useState<string>("");
  const [selectedFeature, setSelectedFeature] = useState<SubdivisionGeoFeature | null>(null);
  const [builderFilter, setBuilderFilter] = useState<number[]>([]);
  const [showPermits, setShowPermits] = useState(true);

  const countiesQ = useQuery<string[]>({
    queryKey: ["counties"],
    queryFn: getCounties,
  });

  const geoQ = useQuery<SubdivisionGeoFeature[]>({
    queryKey: ["subdivision-geojson"],
    queryFn: () => getSubdivisionGeoJSON({}),
  });

  const buildersQ = useQuery<BuilderOut[]>({
    queryKey: ["inventory-builders"],
    queryFn: getInventoryBuilders,
  });

  const permitDashQ = useQuery({
    queryKey: ["permit-dashboard-map"],
    queryFn: () => getPermitDashboard(),
  });

  // Client-side filter by county name + builder filter
  const MIN_LOTS_FOR_MAP = 3;

  // BTR builder IDs — excluded from map display
  const btrIds = useMemo(() => {
    const set = new Set<number>();
    for (const b of buildersQ.data ?? []) {
      if (b.type === "btr") set.add(b.id);
    }
    return set;
  }, [buildersQ.data]);

  const features = useMemo(() => {
    if (!geoQ.data) return [];
    // Strip BTR builders from each feature, recompute lot count
    let result = geoQ.data.map((f) => {
      const builders = f.builders.filter((b) => !btrIds.has(b.builder_id));
      const builder_lot_count = builders.reduce((s, b) => s + b.lot_count, 0);
      return { ...f, builders, builder_lot_count, distinct_builder_count: builders.length };
    });
    result = result.filter((f) => f.builder_lot_count >= MIN_LOTS_FOR_MAP);
    if (selectedCounty) {
      result = result.filter((f) => f.county_name === selectedCounty);
    }
    if (builderFilter.length > 0) {
      result = result.filter((f) =>
        f.builders.some((b) => builderFilter.includes(b.builder_id)),
      );
    }
    return result;
  }, [geoQ.data, selectedCounty, builderFilter, btrIds]);

  // Stable callback for polygon clicks
  const onFeatureClick = useCallback((f: SubdivisionGeoFeature) => {
    setSelectedFeature(f);
  }, []);

  // ---------------------------------------------------------------------------
  // Initialize map once
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!containerRef.current) return;
    if (mapRef.current) return; // already created

    const svgRenderer = L.svg();
    svgRendererRef.current = svgRenderer;

    const map = L.map(containerRef.current, {
      center: [28.5, -81.5], // Central Florida default
      zoom: 10,
      attributionControl: false,
      zoomControl: true,
      renderer: svgRenderer,
    });
    mapRef.current = map;

    // Satellite base layer
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19 }
    ).addTo(map);

    // Road/transportation labels overlay (dimmed so polygons stand out)
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, opacity: 0.4 }
    ).addTo(map);

    layerRef.current = L.layerGroup().addTo(map);
    permitLayerRef.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
      layerRef.current = null;
      permitLayerRef.current = null;
      svgRendererRef.current = null;
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Render polygons whenever features change
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const group = layerRef.current;
    const map = mapRef.current;
    if (!group || !map) return;
    group.clearLayers();

    // Clean up old stripe patterns from previous render
    clearStripePatterns(map);

    if (features.length === 0) return;

    const bounds = L.latLngBounds([]);

    for (const feat of features) {
      // Sort builders by lot_count desc; primary is first
      const sorted = [...feat.builders].sort((a, b) => b.lot_count - a.lot_count);
      const primary = sorted[0];
      const isGracePeriod = feat.builder_lot_count === 0;

      let fillColor: string;
      let strokeColor: string;
      let dashArray: string | undefined;
      let fillOpacity: number;

      if (isGracePeriod) {
        fillColor = "#6B7280";
        strokeColor = "#4B5563";
        fillOpacity = 0.3;
        dashArray = "6 4";
      } else if (sorted.length > 1) {
        // Multi-builder: diagonal stripe pattern
        fillColor = getOrCreateStripePattern(map, sorted);
        strokeColor = getBuilderColor(primary.builder_id).stroke;
        fillOpacity = 0.7;
        dashArray = undefined;
      } else if (primary) {
        const colors = getBuilderColor(primary.builder_id);
        fillColor = colors.fill;
        strokeColor = colors.stroke;
        fillOpacity = 0.6;
        dashArray = undefined;
      } else {
        fillColor = "#9CA3AF";
        strokeColor = "#6B7280";
        fillOpacity = 0.45;
        dashArray = undefined;
      }

      // Build tooltip HTML
      const tooltipLines = [`<strong>${feat.name}</strong>`];
      tooltipLines.push(`<span style="color:#ccc">${feat.builder_lot_count} builder lots</span>`);
      for (const b of sorted.slice(0, 5)) {
        tooltipLines.push(`${b.builder_name}: ${b.lot_count}`);
      }
      if (sorted.length > 5) {
        tooltipLines.push(`<em>+${sorted.length - 5} more</em>`);
      }
      const tooltipHtml = tooltipLines.join("<br>");

      const layer = L.geoJSON(feat.geojson as GeoJSON.GeoJsonObject, {
        style: {
          color: strokeColor,
          weight: 3,
          fillColor,
          fillOpacity,
          dashArray,
        },
      });

      layer.bindTooltip(tooltipHtml, {
        sticky: true,
        direction: "top",
        className: "map-subdivision-tooltip",
      });

      layer.on("click", () => {
        onFeatureClick(feat);
      });

      // Hover highlight
      layer.on("mouseover", () => {
        layer.setStyle({ weight: 4, fillOpacity: Math.min(fillOpacity + 0.15, 0.85) });
      });
      layer.on("mouseout", () => {
        layer.setStyle({ weight: 3, fillOpacity });
      });

      layer.addTo(group);

      try {
        bounds.extend(layer.getBounds());
      } catch {
        // geometry might not produce valid bounds
      }
    }

    // Fit map to polygons
    if (bounds.isValid() && mapRef.current) {
      mapRef.current.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [features, onFeatureClick]);

  // ---------------------------------------------------------------------------
  // Render permit pin layer
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const group = permitLayerRef.current;
    if (!group) return;
    group.clearLayers();

    const points = permitDashQ.data?.map_points;
    if (!showPermits || !points || points.length === 0) return;

    for (const pt of points) {
      const color = pt.status_group === "closed" ? "#22c55e" : "#f59e0b";
      const latlng = L.latLng(pt.latitude, pt.longitude);

      L.circleMarker(latlng, {
        radius: 4,
        color,
        fillColor: color,
        fillOpacity: 0.85,
        weight: 1,
      })
        .bindPopup(
          `<div style="font-size:13px;line-height:1.5">
            <strong>${pt.permit_number}</strong><br/>
            ${pt.address ?? ""}<br/>
            ${pt.jurisdiction} &middot; ${pt.status ?? ""}${pt.issue_date ? `<br/>${pt.issue_date}` : ""}
            ${pt.subdivision !== "Unmatched" ? `<br/>${pt.subdivision}` : ""}
            ${pt.builder !== "Unknown Builder" ? `<br/>${pt.builder}` : ""}
          </div>`,
        )
        .addTo(group);
    }
  }, [permitDashQ.data?.map_points, showPermits]);

  return (
    <div className="fixed inset-0 top-[53px] z-0 flex flex-col">
      {/* Filter bar */}
      <div className="bg-white/90 backdrop-blur border-b border-gray-200 px-4 py-2 flex items-center gap-4 z-[500]">
        <label className="text-sm font-medium text-gray-700">County</label>
        <select
          value={selectedCounty}
          onChange={(e) => setSelectedCounty(e.target.value)}
          className="text-sm border border-gray-300 rounded px-2 py-1 bg-white"
        >
          <option value="">All Counties</option>
          {(countiesQ.data ?? []).map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <label className="text-sm font-medium text-gray-700">Builder</label>
        <select
          multiple
          value={builderFilter.map(String)}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions, (o) => Number(o.value));
            setBuilderFilter(selected);
          }}
          className="text-sm border border-gray-300 rounded px-2 py-1 bg-white min-w-[140px] max-h-24"
        >
          {(buildersQ.data ?? [])
            .filter((b) => b.is_active)
            .sort((a, b) => a.canonical_name.localeCompare(b.canonical_name))
            .map((b) => (
              <option key={b.id} value={b.id}>
                {b.canonical_name}
              </option>
            ))}
        </select>
        {builderFilter.length > 0 && (
          <button
            onClick={() => setBuilderFilter([])}
            className="text-xs text-blue-600 hover:text-blue-800 underline"
          >
            Clear
          </button>
        )}

        <label className="flex items-center gap-1.5 text-sm text-gray-700 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={showPermits}
            onChange={(e) => setShowPermits(e.target.checked)}
            className="rounded border-gray-300"
          />
          Permits
          <span className="inline-block w-2 h-2 rounded-full" style={{ background: "#22c55e" }} />
          <span className="inline-block w-2 h-2 rounded-full" style={{ background: "#f59e0b" }} />
          {showPermits && permitDashQ.data?.map_meta && (
            <span className="text-xs text-gray-400 tabular-nums">
              ({permitDashQ.data.map_meta.count.toLocaleString()})
            </span>
          )}
        </label>

        {geoQ.isLoading && <span className="text-xs text-gray-400">Loading polygons...</span>}
        {geoQ.error && (
          <span className="text-xs text-red-500">
            Failed to load: {(geoQ.error as Error).message}
          </span>
        )}
        {!geoQ.isLoading && !geoQ.error && (
          <span className="text-xs text-gray-400">
            {features.length} subdivision{features.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Map container */}
      <div ref={containerRef} className="flex-1" />

      {/* Detail side panel */}
      {selectedFeature && (
        <DetailPanel
          feature={selectedFeature}
          onClose={() => setSelectedFeature(null)}
        />
      )}
    </div>
  );
}
