# CountyData2 Frontend Visual Redesign - Design Spec

## Purpose

Replace the current thin blue-accent, white-card admin shell with a stronger, more legible product UI that feels like an operational workspace instead of a generic dashboard. The redesign should make dense county data easier to scan, create clearer hierarchy between shell, page content, and detail overlays, and keep the existing information architecture intact.

This spec covers the shared frontend system used by `ui/src/components/Layout.tsx`, `ui/src/pages/DashboardPage.tsx`, `ui/src/pages/InventoryPage.tsx`, `ui/src/pages/TransactionsPage.tsx`, `ui/src/pages/ReviewPage.tsx`, and `ui/src/pages/SubdivisionDetailPage.tsx`, with `ui/src/pages/MapPage.tsx` treated as a deliberate spatial exception rather than part of the generic shell.

## Visual Direction

Use a grounded, report-like visual language:

- Dark, stable shell chrome.
- Warm neutral surfaces instead of pure white cards.
- One strong accent color for interactive state, with restrained use of supportive status colors.
- Softer borders, deeper shadows, and more deliberate spacing to create hierarchy.
- Typography that privileges clarity and density over decoration.

The UI should no longer read as repeated gray boxes on a white canvas. It should feel like an analytical tool with three layers:

1. App shell and navigation.
2. Page-level content surfaces.
3. Exception surfaces such as map canvases and drawers.

The common pages should share a unified card and table language. The map, review/detail drawers, and subdivision detail page should intentionally depart from that language where their tasks require it.

## Design Tokens

Use these tokens as the canonical visual baseline for the redesign.

### Color

- `--bg`: `#f3f4f6` - app background, replacing the current flat `bg-gray-50`.
- `--bg-elevated`: `#e5e7eb` - optional backdrop layer behind large report sections.
- `--surface`: `#faf8f3` - primary cards and panels.
- `--surface-strong`: `#ffffff` - only for overlays, critical forms, and focused data panels.
- `--surface-muted`: `#f5f1ea` - table headers, secondary blocks, and soft grouped sections.
- `--border`: `#d6d3d1` - default divider and panel border.
- `--border-strong`: `#a8a29e` - active borders, focus outlines, and selected states.
- `--text`: `#1f2937` - primary copy.
- `--text-muted`: `#6b7280` - secondary labels and helper text.
- `--text-soft`: `#9ca3af` - de-emphasized metadata.
- `--accent`: `#1d4ed8` - the primary interactive blue, used less frequently but more intentionally than today.
- `--accent-hover`: `#1e40af`.
- `--accent-soft`: `#dbeafe` - selected chips, nav pills, and active table rows.
- `--success`: `#166534`.
- `--warning`: `#a16207`.
- `--danger`: `#b91c1c`.
- `--info`: `#0f766e`.

### Typography

- Headings: `"IBM Plex Sans Condensed", "Arial Narrow", sans-serif`.
- Body and controls: `"Public Sans", "Segoe UI", sans-serif`.
- Data and tabular values: `"IBM Plex Mono", "Consolas", monospace`.
- Page title: `32/36`, `700`.
- Section title: `18/24`, `650`.
- Card title: `14/18`, `700`, uppercase only when the label is genuinely metadata.
- Body text: `14/20`, `400`.
- Dense table text: `13/18`, `400`.
- Metric value: `28/30`, `700`, tabular numbers enabled.

### Spacing

- Base scale: `4, 8, 12, 16, 24, 32, 40, 48`.
- Page gutters: `24px` mobile, `32px` desktop.
- Section padding: `24px` default, `16px` for dense overlays.
- Row padding: `12px` vertical for tables, `8px` vertical for compact lists.

### Radius

- `--radius-sm`: `8px`.
- `--radius-md`: `12px`.
- `--radius-lg`: `16px`.
- Use `radius-md` for standard cards, `radius-lg` for prominent page modules, and `radius-sm` for chips and inputs.

### Elevation

- `--shadow-sm`: `0 1px 2px rgba(15, 23, 42, 0.06)`.
- `--shadow-md`: `0 10px 25px rgba(15, 23, 42, 0.10)`.
- `--shadow-lg`: `0 24px 48px rgba(15, 23, 42, 0.16)`.
- Use elevation sparingly. Most hierarchy should come from spacing, background tone, and border weight, not heavy shadows.

### Motion

- Duration quick: `120ms`.
- Duration standard: `180ms`.
- Duration deliberate: `240ms`.
- Easing: `cubic-bezier(0.2, 0, 0, 1)`.
- Use motion for state change, drawer transitions, hover emphasis, and page-level reveal. Do not animate everything.

## Shell and Navigation

### Layout shell

`ui/src/components/Layout.tsx` should become a darker, more structured app shell:

- Use a deep slate header or side rail instead of a full-width white nav bar.
- Keep the content canvas light, but shift the shell away from the page background so the app frame is distinct.
- Reserve the top shell area for brand, primary navigation, and a compact context indicator.
- Keep the main content width generous, but allow full-bleed exceptions where required.

### Navigation behavior

- Active nav state should be a filled pill or rail segment, not only a pale blue background.
- Navigation items should have stronger contrast and a clearer hover target.
- The active route should be recognizable at a glance without relying on color alone.
- Map navigation should be visually distinct because it leads to an exception surface.

## Shared Pattern Matrix

Use this matrix to keep the redesign consistent across the core surfaces.

| Surface | Pattern role | Primary container | Content density | Exception handling |
|---|---|---|---|---|
| `ui/src/components/Layout.tsx` | Shell and navigation frame | Dark chrome + light content canvas | Low | None |
| `ui/src/pages/DashboardPage.tsx` | Executive overview | Card grid with bold summary modules | Medium | None |
| `ui/src/pages/InventoryPage.tsx` | Operational analysis | Mixed charts, tables, and filters in stacked report sections | High | None |
| `ui/src/pages/TransactionsPage.tsx` | Work queue and investigation | Dense table with filter rail and detail panel | High | Review/detail drawer styling applies |
| `ui/src/pages/ReviewPage.tsx` | Triage queue | Dense table with explicit review actions and detail overlay | High | Review/detail drawer styling applies |
| `ui/src/pages/SubdivisionDetailPage.tsx` | Report-style entity page | Multi-panel report canvas with strong section hierarchy | High | Richer report treatment, not generic cards |
| `ui/src/pages/MapPage.tsx` | Spatial exploration | Full-bleed map canvas with overlay controls | N/A | Full-bleed spatial exception |

## Shared Page Patterns

These rules apply to the common shell-backed pages unless a page-specific section overrides them.

- Page content should start with a clear title block and a short supporting context line.
- Use section cards or panels to group related data, but avoid repeating identical white-card chrome everywhere.
- Prefer fewer, larger containers over many tiny boxes.
- Keep labels muted and values prominent.
- Use tabular numerals for counts, prices, dates, and metrics.
- Use consistent empty/loading/error treatment across all pages.
- Preserve existing route structure and data flow. This is a visual redesign, not an information architecture rewrite.

## Component Patterns

### Cards and panels

- Primary cards use `surface` backgrounds, `border` dividers, and modest radius.
- Secondary cards should be visually quieter: softer background, lighter border, smaller padding.
- Avoid the current default of `bg-white border border-gray-200 rounded-lg` as the universal building block.
- Use stronger section headers with label, summary value, and optional action instead of anonymous card boxes.

### Tables

- Tables should feel dense, readable, and operational.
- Header rows use `surface-muted` with a slightly stronger border.
- Row hover should use a subtle accent tint, not a full blue flood.
- Selected rows should have a clear left rule or background tint.
- Numeric columns align right and use tabular figures.
- Long labels should truncate with tooltips where helpful.

### Filters and controls

- Filter bars should be consolidated and slightly elevated above content.
- Inputs should be compact, with clear focus rings and consistent heights.
- Use chips or segmented controls for quick toggles where the choice set is small.
- Avoid mixing too many control styles within one page.

### Charts and data visualization

- Charts should sit inside report sections, not inside generic cards dropped onto the page.
- Gridlines should be subtle and secondary to the data.
- Axis labels and legends should use `text-muted`, not body-dark.
- Accent colors should be semantic and repeat consistently across modules.

### Badges and status

- Use filled badges only for meaningful status, not as decoration.
- Status colors should be reserved for actual states such as success, warning, failure, or info.
- Neutral metadata badges should use muted surfaces and text rather than bright fills.

### Drawers and overlays

- Drawers should feel denser and more focused than the base page.
- Overlay headers should be sticky, compact, and visually separated from scrollable content.
- Use a slightly stronger shadow and a white or near-white surface for overlays so they read above the report canvas.

## Page-Specific Guidance

### Dashboard

The dashboard should become a summary board, not a collection of same-sized cards.

- Use larger module cards with clearer internal hierarchy.
- Each module card should have a strong title, a primary metric, and secondary supporting stats.
- Highlight action-needed items with a distinct accent strip or badge rail rather than another generic card border.
- The dashboard can remain grid-based, but the cards should vary in visual weight to emphasize importance.

### Inventory

Inventory is a reporting page and should feel denser than the dashboard.

- Stack the trend chart, leaderboard, and drill-down table as report sections with stronger section headers.
- Use a more compact filter/control row at the top.
- Give the drill-down table the most visual weight on the page.
- If multiple sections are visible, use clear spacing and title treatment to avoid the page looking like repeated cards.

### Transactions

Transactions is a task workspace.

- Keep the table dense and scrollable.
- The filter and action controls should live in a clear utility band above the data grid.
- Selected rows, bulk actions, and detail panels should feel like one coherent work area.
- Reduce reliance on pale blue row hovers; use a more subtle hover state and clearer selected state.

### Review

Review should read as a triage queue.

- Keep the filters, counts, and table aligned in a tight workflow layout.
- Review reasons should be visually prioritized so the user can scan the queue quickly.
- The detail panel should feel like a dense investigation overlay, not a second page.
- Keep the export and resolution actions obvious but not visually dominant.

### Subdivision Detail

Subdivision detail should become a richer report-style page, not a stack of small cards.

- Treat the top of the page as an executive summary with identity, status, and key metrics.
- Use a report layout with one prominent hero section and several structured panels below it.
- The map, when present, should feel embedded in the report rather than treated as a generic card.
- Preserve the page's analytical depth by giving the detail sections more hierarchy than the generic shell pages.

### Map

Map is the primary exception and should be treated as a full-bleed spatial workspace.

- The page should not sit inside the same boxed card rhythm as the rest of the app.
- The map canvas fills the available viewport area.
- Filters, legends, and detail affordances float above the map or dock to its edges.
- The detail drawer is part of the map interaction model, not a separate navigation destination.
- The visual language should prioritize spatial clarity over card chrome.

### Review and detail drawers

Review/detail drawers are dense overlays and should be visually separated from both the shell and the base page.

- Use a compact, high-contrast panel with a sticky header.
- Keep the content typography small but legible.
- Group actions, metadata, and derived insights into clear blocks.
- Do not over-space the drawer; density is the point.
- These drawers should remain exception surfaces even if the base page uses the shared card system.

## Motion

Motion should communicate state changes, not ornament.

- Shell navigation changes should crossfade or slide slightly, not bounce.
- Cards may lift subtly on hover with a small upward translate and shadow increase.
- Table rows should tint on hover within the standard duration.
- Drawers should slide in from the edge with the standard ease and a slightly longer duration than hover states.
- Loading skeletons should pulse softly, but avoid flashy shimmer effects on dense pages.
- Map overlays should appear with quick fades so they do not interrupt spatial interaction.

## States

Every major surface must define the same core interaction states.

- Loading: use skeletons or muted placeholders, not only centered text.
- Empty: explain the lack of data in plain language and offer the most likely next action.
- Error: surface the error inside the relevant module, not only as a page-level alert.
- Active/selected: use accent tint plus a structural cue such as border weight or left rail.
- Disabled: reduce contrast and interaction affordance clearly.

## Responsive Behavior

The redesign must work on desktop and mobile without collapsing into cramped white rectangles.

- On mobile, collapse complex grids into single-column stacks.
- Keep shell navigation usable at smaller widths; if the primary nav compresses, preserve route clarity.
- Tables should remain horizontally scrollable when needed, but headers and controls must remain readable.
- Drawers should convert to full-height overlays or bottom-sheet style panels on narrow screens.
- The map page should maintain full-bleed behavior, with controls repositioned to remain reachable on smaller viewports.
- Use responsive spacing that tightens on small screens but does not eliminate hierarchy.

## Files

- Modify: `ui/src/index.css` - introduce color, type, spacing, radius, shadow, and motion tokens.
- Modify: `ui/src/components/Layout.tsx` - establish the new shell and navigation treatment.
- Modify: `ui/src/pages/DashboardPage.tsx` - move from equal-weight cards to summary-board hierarchy.
- Modify: `ui/src/pages/InventoryPage.tsx` - convert the page into a denser report layout with stronger section hierarchy.
- Modify: `ui/src/pages/TransactionsPage.tsx` - restyle filter rail, dense table, and selected-row behavior.
- Modify: `ui/src/pages/ReviewPage.tsx` - align the triage queue and overlay behavior to the new system.
- Modify: `ui/src/components/TransactionDetailPanel.tsx` - convert the drawer into a dense investigative overlay.
- Modify: `ui/src/pages/SubdivisionDetailPage.tsx` - upgrade the page to a richer report treatment.
- Modify: `ui/src/pages/MapPage.tsx` - preserve full-bleed behavior and redesign controls and drawer as spatial overlays.

## Phased Implementation

### Phase 1 - Shell and shared surfaces

- Update `Layout.tsx` to establish the new shell, navigation, and global background.
- Introduce the shared color, typography, radius, shadow, and spacing tokens in `ui/src/index.css`.
- Convert the most repeated card and panel patterns to the new surface language.

### Phase 2 - Core page alignment

- Restyle `DashboardPage.tsx`, `InventoryPage.tsx`, and `TransactionsPage.tsx` to use the new shared page patterns.
- Normalize tables, filters, counts, and section headers.
- Make the common pages look like one product family.

### Phase 3 - Exceptions and overlays

- Special-case `MapPage.tsx` as the full-bleed spatial surface.
- Restyle the review and detail drawers as dense overlays.
- Upgrade `SubdivisionDetailPage.tsx` to the richer report treatment.
- Validate that the exception surfaces remain clearly distinct from the generic shell.

## Out Of Scope

- Rewriting the underlying data model or API contracts.
- Rebuilding map geometry logic or review-resolution logic.
- Changing route structure beyond the visual treatment of the existing pages.
- Introducing a new design system package.
