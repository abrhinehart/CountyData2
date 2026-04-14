import { useEffect, useRef, useState, useCallback, useMemo, type ReactNode } from "react";
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
    <aside className="inspector-drawer map-drawer">
      <div className="inspector-header">
        <div className="min-w-0">
          <p className="inspector-kicker">Subdivision</p>
          <h2 className="inspector-title truncate">{feature.name}</h2>
          <p className="inspector-subtitle">{feature.county_name}</p>
        </div>
        <button
          onClick={onClose}
          className="inspector-close"
          aria-label="Close panel"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="inspector-body">
        <section className="inspector-section flat">
          <div className="section-head">
            <h3 className="section-title">At a glance</h3>
            <span className="badge badge-neutral">Live map</span>
          </div>
          <div className="detail-grid">
            <DetailRow label="Builder lots" value={fmtNum(feature.builder_lot_count) || "0"} />
            <DetailRow label="Builders" value={fmtNum(feature.distinct_builder_count) || "0"} />
            <DetailRow label="County" value={feature.county_name} />
          </div>
        </section>

        <section className="inspector-section">
          <div className="section-head">
            <h3 className="section-title">Builder Mix</h3>
            <span className="badge badge-accent">Parcels</span>
          </div>
          {parcelsQ.isLoading ? (
            <p className="data-note">Loading parcel mix...</p>
          ) : parcelsQ.error ? (
            <p className="data-note text-[var(--danger)]">Failed to load parcels</p>
          ) : builderStats.length === 0 ? (
            <p className="data-note">No parcels tracked.</p>
          ) : (
            <div className="space-y-2">
              {builderStats.slice(0, 12).map((b) => (
                <div key={b.name} className="detail-row">
                  <span className="detail-label truncate" title={b.name}>
                    {b.name}
                  </span>
                  <span className="detail-value tabular-nums">
                    {fmtNum(b.count)}
                    {b.avgValue != null ? ` avg ${fmtDollar(b.avgValue)}` : ""}
                  </span>
                </div>
              ))}
              {builderStats.length > 12 && (
                <p className="data-note">+{builderStats.length - 12} more builders</p>
              )}
            </div>
          )}
        </section>

        <section className="inspector-section">
          <div className="section-head">
            <h3 className="section-title">Sales Velocity</h3>
            <span className="badge badge-success">Trend</span>
          </div>
          {salesQ.isLoading ? (
            <p className="data-note">Loading sales history...</p>
          ) : salesQ.error ? (
            <p className="data-note text-[var(--danger)]">Failed to load sales</p>
          ) : monthlyVelocity.length === 0 ? (
            <p className="data-note">No sales recorded.</p>
          ) : (
            <div className="space-y-2">
              {monthlyVelocity.slice(0, 12).map(([month, count]) => (
                <div key={month} className="detail-row">
                  <span className="detail-label">{month}</span>
                  <span className="detail-value tabular-nums">{count}</span>
                </div>
              ))}
              {monthlyVelocity.length > 12 && (
                <p className="data-note">+{monthlyVelocity.length - 12} more months</p>
              )}
            </div>
          )}
        </section>

        {actions.length > 0 && (
          <section className="inspector-section">
            <div className="section-head">
              <h3 className="section-title">Commission Actions</h3>
              <span className="badge badge-warning">{actions.length}</span>
            </div>
            <div className="space-y-2">
              {actions.slice(0, 6).map((a) => (
                <div key={a.id} className="surface-muted rounded-[var(--radius-lg)] border border-[var(--border-subtle)] px-3 py-2.5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-[0.72rem] uppercase tracking-[0.18em] text-[var(--text-muted)]">
                        {a.meeting_date}
                      </p>
                      <p className="truncate text-sm text-[var(--text-strong)]">
                        {a.approval_type.replace(/_/g, " ")}
                      </p>
                    </div>
                    {a.outcome && (
                      <span
                        className={`badge ${
                          a.outcome === "approved"
                            ? "badge-success"
                            : a.outcome === "denied"
                              ? "badge-danger"
                              : "badge-neutral"
                        }`}
                      >
                        {a.outcome}
                      </span>
                    )}
                  </div>
                </div>
              ))}
              {actions.length > 6 && <p className="data-note">+{actions.length - 6} more</p>}
            </div>
          </section>
        )}

        <Link
          to={`/subdivisions/${feature.id}`}
          className="button-primary w-full justify-center"
        >
          View full details
        </Link>
      </div>
    </aside>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-row">
      <span className="detail-label">{label}</span>
      <span className="detail-value">{value}</span>
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

  const permitDashQ = useQuery<PermitDashboard>({
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
    <div className="map-page fixed inset-0 top-[var(--shell-height)] z-0 overflow-hidden">
      <div ref={containerRef} className="absolute inset-0" />

      <div className="pointer-events-none absolute inset-x-0 top-0 z-[500]">
        <div className="mx-auto flex w-full max-w-[var(--shell-max)] flex-col gap-3 px-4 pb-4 pt-4 sm:px-6 lg:px-8">
          <div className="map-toolbar pointer-events-auto">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="min-w-0 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="badge badge-accent">Spatial exception</span>
                  <span className="badge badge-neutral">Live overlays</span>
                </div>
                <div>
                  <p className="page-kicker">Map workspace</p>
                  <h1 className="page-title">Subdivision atlas</h1>
                  <p className="page-subtitle">
                    Filter by county or builder, inspect polygon mix, and layer permit activity over the map.
                  </p>
                </div>
              </div>

              <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-1 xl:min-w-[15rem]">
                <StatCard
                  label="Visible subdivisions"
                  value={fmtNum(features.length) || "0"}
                  meta={selectedCounty || "All counties"}
                />
                <StatCard
                  label="Builder filters"
                  value={fmtNum(builderFilter.length) || "0"}
                  meta={builderFilter.length > 0 ? "Active" : "None selected"}
                />
                <StatCard
                  label="Permit points"
                  value={fmtNum(permitDashQ.data?.map_meta?.count ?? 0) || "0"}
                  meta={showPermits ? "Layer on" : "Layer hidden"}
                />
              </div>
            </div>

            <div className="grid gap-3 xl:grid-cols-[minmax(0,1.1fr)_minmax(14rem,0.9fr)]">
              <div className="surface-muted rounded-[var(--radius-xl)] border border-[var(--border-subtle)] p-3">
                <div className="filter-grid">
                  <FieldLabel label="County">
                    <select
                      value={selectedCounty}
                      onChange={(e) => setSelectedCounty(e.target.value)}
                      className="form-control"
                    >
                      <option value="">All counties</option>
                      {(countiesQ.data ?? []).map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </select>
                  </FieldLabel>

                  <FieldLabel label="Builder">
                    <select
                      multiple
                      value={builderFilter.map(String)}
                      onChange={(e) => {
                        const selected = Array.from(e.target.selectedOptions, (o) => Number(o.value));
                        setBuilderFilter(selected);
                      }}
                      className="form-control min-h-[6.5rem]"
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
                  </FieldLabel>

                  <FieldLabel label="Permits">
                    <button
                      type="button"
                      onClick={() => setShowPermits((value) => !value)}
                      className={`chip-pill justify-between ${showPermits ? "active" : ""}`}
                    >
                      <span className="inline-flex items-center gap-2">
                        <span className="inline-block h-2 w-2 rounded-full bg-[var(--success)]" />
                        Show permit layer
                      </span>
                      <span>{showPermits ? "On" : "Off"}</span>
                    </button>
                  </FieldLabel>
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setBuilderFilter([])}
                    className="button-ghost"
                    disabled={builderFilter.length === 0}
                  >
                    Clear builder filters
                  </button>
                  <span className="data-note">
                    {geoQ.isLoading
                      ? "Loading polygons..."
                      : geoQ.error
                        ? `Failed to load: ${(geoQ.error as Error).message}`
                        : `${features.length} subdivision${features.length !== 1 ? "s" : ""} visible`}
                  </span>
                </div>
              </div>

              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
                <div className="surface-card map-stat p-3">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
                    <p className="text-sm font-medium text-[var(--text-strong)]">Polygon mix</p>
                  </div>
                  <p className="data-note mt-1">Multi-builder parcels use striped fills; grace-period areas stay muted.</p>
                </div>
                <div className="surface-card map-stat p-3">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-[var(--success)]" />
                    <p className="text-sm font-medium text-[var(--text-strong)]">Permit pins</p>
                  </div>
                  <p className="data-note mt-1">Green marks closed permits and amber marks open work.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {selectedFeature && (
        <>
          <div
            className="drawer-scrim"
            aria-hidden="true"
            onClick={() => setSelectedFeature(null)}
          />
          <DetailPanel
            feature={selectedFeature}
            onClose={() => setSelectedFeature(null)}
          />
        </>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  meta,
}: {
  label: string;
  value: string;
  meta: string;
}) {
  return (
    <div className="map-stat">
      <span className="hero-label">{label}</span>
      <span className="hero-value">{value}</span>
      <span className="hero-meta">{meta}</span>
    </div>
  );
}

function FieldLabel({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field-stack">
      <span className="field-label">{label}</span>
      {children}
    </label>
  );
}
