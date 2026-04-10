"""
Subdivision geometry lookup using the shared PostGIS database.

Since PT now lives inside CountyData2, no separate database connection
is needed -- the caller passes the same psycopg2 connection used everywhere.
"""
from __future__ import annotations


JURISDICTION_TO_COUNTY = {
    "Bay County": "Bay",
    "Panama City": "Bay",
    "Panama City Beach": "Bay",
    "Polk County": "Polk",
}


class SubdivisionGeometryLookup:
    """Context-managed wrapper around a shared psycopg2 connection."""

    def __init__(self, conn) -> None:
        self._conn = conn

    def __enter__(self) -> "SubdivisionGeometryLookup":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Connection is owned by the caller; we do not close it.
        pass

    def lookup(
        self,
        *,
        latitude: float | None,
        longitude: float | None,
        jurisdiction_name: str | None,
    ) -> dict | None:
        county_name = JURISDICTION_TO_COUNTY.get(jurisdiction_name or "")
        if (
            county_name is None
            or latitude is None
            or longitude is None
        ):
            return None

        with self._conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.canonical_name, c.name AS county
                FROM subdivisions s
                JOIN counties c ON c.id = s.county_id
                WHERE c.name = %s AND s.geom IS NOT NULL
                AND ST_Intersects(s.geom, ST_SetSRID(ST_Point(%s, %s), 4326))
                ORDER BY ST_Area(s.geom::geography) ASC
                LIMIT 1
                """,
                (county_name, longitude, latitude),
            )
            row = cur.fetchone()

        if row is None:
            return None
        return {
            "name": row[0],
            "county": row[1],
        }


def lookup_subdivision_for_point(
    conn,
    *,
    latitude: float | None,
    longitude: float | None,
    jurisdiction_name: str | None,
) -> dict | None:
    """Convenience one-shot lookup."""
    try:
        with SubdivisionGeometryLookup(conn) as lookup:
            return lookup.lookup(
                latitude=latitude,
                longitude=longitude,
                jurisdiction_name=jurisdiction_name,
            )
    except Exception:
        return None
