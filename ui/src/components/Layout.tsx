import { NavLink, Outlet, useLocation } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/subdivisions", label: "Subdivisions" },
  { to: "/transactions", label: "Transactions" },
  { to: "/inventory", label: "Inventory" },
  { to: "/permits", label: "Permits" },
  { to: "/commission", label: "Commission" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/map", label: "Map", tone: "map" },
  { to: "/health", label: "Health" },
];

function routeContext(pathname: string): string {
  if (pathname === "/") return "Unified county intelligence workspace";
  if (pathname.startsWith("/transactions")) return "Sales ETL queue and deed investigation";
  if (pathname.startsWith("/review")) return "Flagged transaction triage";
  if (pathname.startsWith("/inventory")) return "Builder lot and parcel reporting";
  if (pathname.startsWith("/permits")) return "Permit scraping and watchlist tracking";
  if (pathname.startsWith("/commission")) return "Entitlement and agenda monitoring";
  if (pathname.startsWith("/pipeline")) return "Operational runs and exports";
  if (pathname.startsWith("/subdivisions/")) return "Subdivision report canvas";
  if (pathname.startsWith("/subdivisions")) return "Builder-active subdivision index";
  if (pathname.startsWith("/map")) return "Spatial overlay workspace";
  if (pathname.startsWith("/health")) return "Platform diagnostics";
  return "CountyData2 operational workspace";
}

export default function Layout() {
  const location = useLocation();
  const isMap = location.pathname.startsWith("/map");

  return (
    <div className="app-shell">
      <nav className="shell-nav">
        <div className="shell-nav-inner">
          <div className="brand-lockup">
            <span className="brand-kicker">County Intelligence</span>
            <span className="brand-name">CountyData2</span>
            <span className="brand-context">{routeContext(location.pathname)}</span>
          </div>
          <div className="shell-links">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.to === "/"}
                className={({ isActive }) =>
                  `${isActive ? "nav-link active" : "nav-link"}${link.tone === "map" ? " map-link" : ""}`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>
      <main className={isMap ? "shell-main shell-main--map" : "shell-main"}>
        <Outlet />
      </main>
    </div>
  );
}
