/** Brand colors for top national builders. Keyed by builder ID. */
const BUILDER_BRAND_COLORS: Record<number, { fill: string; stroke: string; label: string }> = {
  1:   { fill: "#D64309", stroke: "#A33307", label: "DR Horton" },
  3:   { fill: "#003DA5", stroke: "#002B75", label: "Lennar" },
  12:  { fill: "#00843D", stroke: "#005C2A", label: "Pulte" },
  11:  { fill: "#E4002B", stroke: "#B30022", label: "Meritage" },
  10:  { fill: "#F7941D", stroke: "#C47516", label: "LGI" },
  13:  { fill: "#7B2D8E", stroke: "#5C2169", label: "Starlight" },
  15:  { fill: "#1B365D", stroke: "#122541", label: "NVR" },
  9:   { fill: "#B8860B", stroke: "#8B6508", label: "DSLD" },
  2:   { fill: "#2E8B57", stroke: "#1F5F3B", label: "Adams Homes" },
  5:   { fill: "#DC143C", stroke: "#A30E2D", label: "Holiday" },
  8:   { fill: "#4682B4", stroke: "#335F80", label: "Maronda" },
  244: { fill: "#556B2F", stroke: "#3D4D21", label: "Clayton" },
  339: { fill: "#CD853F", stroke: "#9A632F", label: "Century" },
  16:  { fill: "#8B0000", stroke: "#630000", label: "Hovnanian" },
  14:  { fill: "#008B8B", stroke: "#006363", label: "West Bay" },
};

const OTHER_STYLE = { fill: "#9CA3AF", stroke: "#6B7280", label: "Other" };

export function getBuilderColor(builderId: number): { fill: string; stroke: string; label: string } {
  return BUILDER_BRAND_COLORS[builderId] ?? OTHER_STYLE;
}

export { BUILDER_BRAND_COLORS, OTHER_STYLE };
