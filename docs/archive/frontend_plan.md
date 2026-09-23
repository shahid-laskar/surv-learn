# Comprehensive Frontend Enhancement Plan — Sarvanetra Surveillance

A full audit and upgrade plan to bring the frontend from MVP-level to commercial-grade surveillance software. Covers the video player, every page, shared infrastructure, and UX polish.

---

## User Review Required

> [!IMPORTANT]
> This is a **large-scope plan** broken into **7 phases**. Each phase is independently deployable.
> I recommend approving phases sequentially so we can validate each before moving on. Please confirm which phases to prioritize or if any features should be dropped/deferred.

> [!WARNING]
> **Phase 1 (Video Player)** touches the core `HLSPlayer.tsx` component used by LiveView, Playback, and MiniTile. It is the highest-impact change and should be done first and tested thoroughly before other phases begin.

---

## Open Questions

1. **Snapshot API** — Does the backend expose a snapshot/thumbnail endpoint (e.g., `/cameras/{cam_id}/snapshot`)? If not, we can capture snapshots client-side via `<canvas>` from the video element. Which approach do you prefer?
2. **Clip Export** — For the "export clip" feature in Playback, should we use the existing `playback_url` download, or do you want server-side clip extraction with custom start/end times?
3. **Notification System** — The header has a bell icon with a static red dot. Should notifications be backed by a real API/WebSocket, or should we start with a client-side notification queue (e.g., toast-based motion alerts)?
4. **Mobile Responsiveness** — The sidebar is `hidden lg:flex`. Should we add a hamburger menu for mobile/tablet, or is this primarily a desktop application?
5. **Dark/Light Theme** — The design system is dark-only. Should we plan for a light theme toggle, or keep dark-only for V1?
6. **Toast Library** — `react-hot-toast` is already installed but unused. Should we use it for operation feedback (camera created, user added, etc.)?
7. **Zustand** — It's in `package.json` but not used anywhere. Should we adopt it for global state (selected camera, user preferences, notification queue)?

---

## Proposed Changes

### Phase 1: Commercial-Grade Video Player

The current `HLSPlayer.tsx` is a minimal wrapper — no controls overlay, no zoom, no speed control, no frame-stepping, no snapshot, no latency display. The `FeaturedFeed` in LiveView has basic play/pause/mute but nothing else. The Playback page uses a bare `<video controls>`.

---

#### [MODIFY] [HLSPlayer.tsx](file:///opt/surv-learn/surv/frontend/src/components/HLSPlayer.tsx)

**Current gaps:**
- No zoom (digital pan & zoom)
- No playback speed control
- No frame step forward/backward
- No snapshot capture
- No latency indicator (for live streams)
- No bitrate/quality selector
- No picture-in-picture support
- No keyboard shortcuts

**Changes:**
- Add a `VideoControls` overlay component rendered inside HLSPlayer when `showControls` prop is true
- Expose new ref methods: `snapshot()`, `setPlaybackRate()`, `setZoom()`, `stepFrame()`
- Add `HLSPlayerRef` extensions for external control

#### [NEW] [VideoControls.tsx](file:///opt/surv-learn/surv/frontend/src/components/VideoControls.tsx)

A comprehensive floating controls overlay (auto-hide on idle, show on hover/tap) with:

| Control | Description |
|---------|-------------|
| **Play / Pause** | Toggle with spacebar shortcut |
| **Mute / Volume slider** | Click to toggle, hover to show slider |
| **Playback speed** | Dropdown: 0.25×, 0.5×, 1×, 1.5×, 2×, 4×, 8× |
| **Frame step** | ◀ Frame / Frame ▶ buttons (pause + seek ±1 frame) |
| **Digital zoom** | Scroll-wheel zoom (1×–8×), click-drag to pan within zoomed view |
| **Snapshot** | Capture current frame to PNG, download or copy to clipboard |
| **Fullscreen** | Toggle fullscreen with `F` shortcut |
| **Picture-in-Picture** | Float the video in a system PiP window |
| **Live latency** | Show current latency in ms (live mode only, from `hls.latency`) |
| **Quality selector** | If HLS has multiple qualities, show a quality picker (Auto / 720p / 1080p etc.) |
| **Timestamp OSD** | Show current timestamp overlay (toggleable) |
| **Keyboard shortcuts** | Space=play/pause, F=fullscreen, M=mute, ←/→=seek ±5s, ,/.=frame step, +/-=speed |

#### [NEW] [useVideoZoom.ts](file:///opt/surv-learn/surv/frontend/src/hooks/useVideoZoom.ts)

Custom hook to manage digital zoom state:
- `zoomLevel` (1–8), `panOffset` ({x, y})
- Wheel handler to zoom at cursor position
- Drag handler to pan when zoomed
- Double-click to reset zoom
- Applies CSS `transform: scale() translate()` to the video element

#### [NEW] [useVideoKeyboard.ts](file:///opt/surv-learn/surv/frontend/src/hooks/useVideoKeyboard.ts)

Centralized keyboard shortcut handler for the video player:
- Prevents conflict with form inputs
- Supports all shortcuts listed above
- Shows brief toast for actions (e.g., "2× speed")

---

#### [MODIFY] [LiveView.tsx](file:///opt/surv-learn/surv/frontend/src/pages/LiveView.tsx)

- Replace the manual `FeaturedFeed` live bar with the new `VideoControls` (remove ~40 lines of duplicate control logic)
- Add timestamp OSD display on the featured feed
- Add right-click context menu: Snapshot, Copy stream URL, Open in PiP, View in Playback

#### [MODIFY] [Playback.tsx](file:///opt/surv-learn/surv/frontend/src/pages/Playback.tsx)

- Replace bare `<video controls>` with `HLSPlayer` + `VideoControls` for consistent experience
- Add playback speed controls in the player
- Add frame-step navigation
- Add a seek bar synced with the Timeline component (scrub within segment)
- Add clip export: select start/end time within a segment, download clip

---

### Phase 2: Enhanced Timeline & Playback Experience

The Timeline is a basic canvas with no zoom, no scrubbing, and no motion-event overlay.

---

#### [MODIFY] [Timeline.tsx](file:///opt/surv-learn/surv/frontend/src/components/Timeline.tsx)

- **Scroll-to-zoom**: Mouse wheel zooms the timeline (1h → 15min → 5min → 1min view)
- **Drag-to-pan**: Click-drag to scrub the visible window
- **Hover tooltip**: Show exact time + segment info on hover
- **Motion event markers**: Overlay red markers for motion events on the timeline
- **Current playback position**: Animate a green playhead cursor that moves during playback
- **Minimap**: A thin full-day overview bar above the zoomed timeline
- **Segment gap indicators**: Visually distinguish gaps vs. continuous recording
- **Responsive resizing**: Use `ResizeObserver` instead of fixed `width={900}`

#### [MODIFY] [Playback.tsx](file:///opt/surv-learn/surv/frontend/src/pages/Playback.tsx)

- Add continuous playback across segments (auto-advance to next segment)
- Add date range picker (multi-day timeline view)
- Add export controls: "Export all segments for this date" bulk download
- Add a thumbnail preview strip (if backend supports thumbnails)
- Add segment metadata display (file size, codec info)

---

### Phase 3: LiveView Grid & Multi-Camera Improvements

---

#### [MODIFY] [LiveView.tsx](file:///opt/surv-learn/surv/frontend/src/pages/LiveView.tsx)

**Grid layout upgrades:**
- Add 3×3 (9-camera) and custom grid layouts
- Add drag-and-drop to rearrange camera positions in grid
- Add camera name label toggle on grid tiles
- Remember grid preference in `localStorage`

**Camera list sidebar (new panel):**
- Searchable/filterable camera list panel (slide-in from right)
- Filter by: online/offline, group, organization, motion status
- Drag from list → drop onto grid slot

**Live features:**
- Double-click any grid tile → expand to featured view
- Split-screen: compare two cameras side-by-side
- Auto-cycle mode: rotate through cameras every N seconds (configurable)
- Audio selector: choose which camera's audio is active

**FeaturedFeed enhancements:**
- Add the new `VideoControls` (Phase 1)
- Add recording indicator (if camera is actively recording)
- Add camera info popover (IP, port, last seen, uptime, motion status)

---

### Phase 4: Global UX & Navigation Improvements

---

#### [MODIFY] [Sidebar.tsx](file:///opt/surv-learn/surv/frontend/src/components/Sidebar.tsx)

- **Collapsible sidebar**: Icon-only mode (toggle with button or `[` shortcut)
- **Sidebar on mobile**: Hamburger menu → slide-in drawer
- **Camera quick-list improvements**: Show camera name (not just ID), online count badge
- **Active motion indicator**: Pulsing icon on sidebar when active motion detected
- **Breadcrumb context**: Show which camera/page is currently active

#### [MODIFY] [App.tsx](file:///opt/surv-learn/surv/frontend/src/App.tsx)

**Header improvements:**
- **Command palette** (`Ctrl+K` or `/`): Quick navigate to any camera, page, or action
- **Notification dropdown**: Replace static bell with a real dropdown showing recent events (motion alerts, camera status changes, system alerts)
- **User profile dropdown**: Settings, theme toggle, change password, session info
- **Global search**: Search cameras by ID, name, IP, or location
- **Breadcrumbs**: Show navigation context (e.g., "Playback > CAMKRTVM00001 > 2026-07-13")

#### [NEW] [CommandPalette.tsx](file:///opt/surv-learn/surv/frontend/src/components/CommandPalette.tsx)

- Modal triggered by `Ctrl+K`
- Search: cameras, pages, recent motion events, users
- Actions: navigate to camera, open playback, take snapshot
- Fuzzy matching with keyboard navigation

#### [NEW] [NotificationDropdown.tsx](file:///opt/surv-learn/surv/frontend/src/components/NotificationDropdown.tsx)

- Recent motion alerts with camera name and timestamp
- Camera online/offline status changes
- System warnings (storage full, service down)
- Mark as read, clear all
- Link to relevant page (click motion alert → opens Playback)

#### [NEW] [UserProfileDropdown.tsx](file:///opt/surv-learn/surv/frontend/src/components/UserProfileDropdown.tsx)

- Username, role, permissions summary
- Change password form
- Session info (token expiry, last login)
- Logout button (moved from sidebar footer)
- Preferences: default grid size, auto-cycle interval, etc.

---

### Phase 5: Toast Notifications & Feedback System

Currently, no operation feedback is shown anywhere. Creating a camera, deleting a user — nothing confirms success or failure beyond form-level error messages.

---

#### [NEW] [ToastProvider.tsx](file:///opt/surv-learn/surv/frontend/src/components/ToastProvider.tsx)

- Wire up `react-hot-toast` (already installed) with Sarvanetra-themed styling
- Dark glass-morphism toasts matching the design system
- Success / Error / Warning / Info variants
- Auto-dismiss with undo support for destructive actions

#### [MODIFY] Multiple pages — add toast feedback to:

| Page | Toast triggers |
|------|---------------|
| **Cameras** | Created ✓, Updated ✓, Deleted ✓, Error ✗ |
| **Users** | Created ✓, Role assigned ✓, Role removed ✓ |
| **Customers** | Created ✓, Site added ✓ |
| **Organizations** | Node created ✓ |
| **Roles** | Role created ✓, Permission assigned/removed ✓ |
| **CameraGroups** | Group created ✓, Camera added ✓ |
| **NvrFleet** | Provisioned ✓, Decommissioned ✓ |
| **LiveView** | Snapshot saved ✓, Stream error ✗ |

---

### Phase 6: Data Tables, Filtering & Pagination

All table-based pages use minimal inline tables with no sorting, no searching, no proper pagination, and `confirm()` for delete operations.

---

#### [NEW] [DataTable.tsx](file:///opt/surv-learn/surv/frontend/src/components/DataTable.tsx)

A reusable data table component with:
- **Column sorting** (click header to sort asc/desc)
- **Search/filter bar** (full-text search across visible columns)
- **Pagination** (proper page buttons with page size selector: 25/50/100)
- **Row selection** (checkbox column for bulk actions)
- **Column visibility** toggle
- **Empty state** with icon and message
- **Loading skeleton** rows during fetch
- **Sticky header** with proper z-index
- **Responsive**: horizontal scroll on small screens

#### [NEW] [ConfirmDialog.tsx](file:///opt/surv-learn/surv/frontend/src/components/ConfirmDialog.tsx)

- Replace all `confirm()` calls with a styled modal dialog
- Destructive action variant (red button, warning icon)
- Input confirmation for high-risk actions (type camera ID to confirm delete)

#### [NEW] [LoadingSkeleton.tsx](file:///opt/surv-learn/surv/frontend/src/components/LoadingSkeleton.tsx)

- Pulsing skeleton rows matching table layout
- Use for initial page load states (replace bare "Loading..." text)

#### Pages to refactor with `DataTable`:

| Page | Enhancements |
|------|-------------|
| **Cameras** | Sortable by status/name/IP, search by ID/name/IP, bulk delete, skeleton loading |
| **Users** | Sortable by username/type/status, search, bulk role assignment |
| **Customers** | Sortable by name/type/status, search by name/code/email |
| **AuditLog** | Date range picker, export to CSV, sortable columns, proper pagination with offset |
| **MotionEvents** | Date range filter, sortable by time/camera/duration, export |
| **Health** | Sortable camera list, uptime percentage bars |
| **CameraGroups** | Show camera count per group, sortable |
| **Organizations** | Search within tree, collapse all / expand all |

---

### Phase 7: Polish, Accessibility & Performance

---

#### [MODIFY] [index.css](file:///opt/surv-learn/surv/frontend/src/index.css)

- Add focus-visible ring styles for keyboard navigation
- Add `prefers-reduced-motion` media query to disable animations
- Add print stylesheet (for exporting audit logs / reports)
- Add CSS transitions for page switches

#### [NEW] [usePreferences.ts](file:///opt/surv-learn/surv/frontend/src/hooks/usePreferences.ts)

Zustand-based user preferences store (persisted to localStorage):
- Default grid layout (1×1 / 2×2 / 4×4)
- Auto-cycle interval
- Sidebar collapsed state
- Mute preference
- Playback speed preference
- Timestamp format (12h/24h)
- Notification sound toggle

#### Accessibility improvements (across all components):

- Add `aria-label` to all icon-only buttons
- Add `role="alert"` to error/status messages
- Ensure focus management in modals (trap focus, return on close)
- Add skip-to-content link
- Ensure color contrast meets WCAG AA (verify OKLCH values)
- Add `aria-live` regions for real-time status updates

#### Performance improvements:

- **Lazy load pages** with `React.lazy()` + `Suspense` (all routes)
- **Virtualized tables** for large datasets (AuditLog, MotionEvents) using `@tanstack/react-virtual`
- **Debounced search** inputs (300ms debounce)
- **Memoize expensive components** (`React.memo` on grid tiles, table rows)
- **Reduce HLS player instances** in grid: only create HLS instances for visible tiles
- **Image placeholders**: Show last-known thumbnail for offline cameras instead of blank

---

## Summary: Files Changed by Phase

| Phase | New Files | Modified Files |
|-------|-----------|----------------|
| 1 — Video Player | `VideoControls.tsx`, `useVideoZoom.ts`, `useVideoKeyboard.ts` | `HLSPlayer.tsx`, `LiveView.tsx`, `Playback.tsx` |
| 2 — Timeline | — | `Timeline.tsx`, `Playback.tsx` |
| 3 — LiveView Grid | — | `LiveView.tsx` |
| 4 — Navigation/UX | `CommandPalette.tsx`, `NotificationDropdown.tsx`, `UserProfileDropdown.tsx` | `Sidebar.tsx`, `App.tsx` |
| 5 — Toasts | `ToastProvider.tsx` | All CRUD pages (8 files) |
| 6 — Data Tables | `DataTable.tsx`, `ConfirmDialog.tsx`, `LoadingSkeleton.tsx` | All table pages (8 files) |
| 7 — Polish | `usePreferences.ts` | `index.css`, `App.tsx`, all pages |

---

## Verification Plan

### Automated Tests
- `npm run build` — ensure no TypeScript errors after each phase
- `npm run lint` — ensure no lint regressions

### Manual Verification
- **Phase 1**: Test all player controls in LiveView (featured feed) and Playback. Test zoom, speed, snapshot, PiP, keyboard shortcuts. Verify on Chrome, Firefox, Safari.
- **Phase 2**: Test timeline zoom/pan, hover tooltips, click-to-seek, playhead animation, and cross-segment playback.
- **Phase 3**: Test all grid layouts (1–4×4), drag-rearrange, auto-cycle, double-click expand, camera search panel.
- **Phase 4**: Test Ctrl+K command palette, notification dropdown, sidebar collapse, mobile hamburger menu, breadcrumbs.
- **Phase 5**: Trigger every CRUD operation and verify toast appears with correct message and styling.
- **Phase 6**: Test sort, search, pagination, and bulk actions on every table page. Test ConfirmDialog on delete operations.
- **Phase 7**: Tab through entire app (keyboard-only navigation), verify `prefers-reduced-motion`, test lazy loading, check large dataset performance.
