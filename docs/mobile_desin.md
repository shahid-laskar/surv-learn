# Sarvanetra Mobile — Professional App Specification
## Embedded WireGuard Remote Access + Photo-Based Camera Onboarding
*Expo / React Native, current (2026) industry-standard stack*

This document extends `sarvanetra_edge_vpn_extension_plan.md` §4 by committing to **Option B — embedded WireGuard SDK** instead of a companion-app VPN, and adds a new field-operations feature: onboarding a camera remotely by photographing its serial-number label. It is a specification for engineering, not code — every native piece named here is a real, currently-maintained library so this can go straight into a sprint plan.

---

## 0. The one thing to align on before anything else: "Expo Go" vs. a real build

> [!IMPORTANT]
> **Embedding a VPN and running on-device OCR both require custom native code (Swift + Kotlin). Expo Go — the sandbox app on the App Store/Play Store — cannot load custom native modules; it only supports the fixed set of modules Expo ships pre-compiled into it.** This is not a limitation you can configure around; it's how Expo Go works. It applies to VPN packet-tunnel providers and to ML Kit frame-processor OCR alike.
>
> This does **not** mean giving up Expo. It means using Expo the way virtually every serious Expo app with camera/VPN/Bluetooth features does in 2026: **Expo (React Native) + a custom Development Build produced by EAS Build, using the Expo Modules API and Config Plugins** to add the two pieces of native code this app needs. You keep 100% of Expo's developer experience — Expo Router, EAS Update for JS-only OTA pushes, `npx expo start`, TypeScript config, autolinking — you just install your own Dev Client on test devices instead of the generic Expo Go app, and ship a normal EAS-built binary to the stores. This is the standard, supported Expo workflow for exactly this class of app; it is not "ejecting" and does not mean abandoning Expo's tooling.

So: **"Expo, React Native, latest industry standard" = Expo SDK with a custom Dev Client + EAS Build, not Expo Go.** Everything below assumes that setup.

---

## 1. Baseline Stack (2026 current)

| Layer | Choice | Why |
|---|---|---|
| Framework | Expo SDK (latest stable), **New Architecture (Fabric + TurboModules) on by default** | Standard as of recent SDKs; required for the Nitro-based camera/OCR modules below |
| Navigation | Expo Router (file-based) | Now the default/recommended navigation approach for Expo apps |
| Language | TypeScript, strict mode | Non-negotiable for a codebase with native module boundaries |
| Native module authoring | **Expo Modules API** (Swift + Kotlin) + **Config Plugins** | Expo's own recommended path for "library doesn't do what I need" — generates and patches `Info.plist`/`AndroidManifest.xml`/extension targets automatically on `expo prebuild`, so the VPN extension target and OCR native deps stay reproducible rather than hand-edited Xcode/Gradle state |
| Data fetching/cache | TanStack Query | Matches the pattern already used on the existing Sarvanetra web frontend — one mental model across web and mobile |
| Local/UI state | Zustand | Lightweight, avoids Redux boilerplate for what's mostly server state |
| Secure token/key storage | `expo-secure-store` (iOS Keychain / Android Keystore-backed) | JWT, refresh token, and the device's WireGuard private key must never touch plain storage or JS-accessible AsyncStorage |
| Biometric app-lock | `expo-local-authentication` | Sensitive content (live camera feeds); require Face ID/fingerprint to reopen after backgrounding |
| Push notifications | `expo-notifications` + FCM (Android) / APNs (iOS) | Motion/offline alerts (ties into the existing Phase 9 `notifier.py` and Phase 14 alerting) |
| Camera capture (simple) | `expo-camera` (`CameraView`) | Built-in QR/barcode scanning works even before you add any custom native module — see §3 |
| Camera capture (advanced) | **React Native Vision Camera v4** (Nitro Modules-based) | The only practical choice once you need per-frame access for OCR — confirmed as the 2026 community consensus for "does the app need real-time frame analysis (OCR, ML)?" |
| On-device OCR | ML Kit Text Recognition via a Vision Camera v4 frame-processor plugin (e.g. the actively-maintained `react-native-vision-camera-ocr-plus`, or an equivalent first-party Nitro plugin built the same way) | Fully offline, low-latency, no per-scan cloud cost or data exposure |
| Error/crash observability | Sentry (React Native SDK) | Native crashes (VPN extension, camera pipeline) need native-level stack traces, not just JS ones |
| CI/CD | EAS Build (dev/preview/production profiles) + EAS Update for JS-only hotfixes | Standard Expo release pipeline; **note in §5.3** which changes qualify for OTA vs. require a full store release |
| Design system | A small custom token set (React Native Paper *or* Tamagui as the primitive layer) sharing color tokens with the existing web app's Tailwind v4 `@theme` palette (`--color-accent`, `--color-online`, `--color-alert`, etc.) | Visual consistency between the web dashboard and the mobile app reinforces it as one product |

---

## 2. Embedded WireGuard — Deep Design

### 2.1 Why embedded (confirming Option B) and what it changes vs. the companion-app plan

Embedding means the Sarvanetra app itself brings the tunnel up and down — no second app, no manual QR-into-Tailscale-app step, no explaining VPN concepts to a non-technical customer. The trade-off is real native engineering and an App Store review path that's stricter for anything holding the Network Extension / VpnService entitlement. That trade-off is worth it for a commercial product; it is not worth it for an internal ops tool, so if a purely-internal BSNL staff build is ever needed in parallel, the companion-app route from the original plan remains a valid lighter-weight fallback for that specific audience.

### 2.2 Don't embed a random npm WireGuard wrapper — build a thin first-party module on the official libraries

Searching the ecosystem turns up several small `react-native-wireguard-*` packages. Treat these as **reference implementations to read, not dependencies to ship** — most are single-maintainer, inconsistently updated, and you do not want your remote-access security boundary depending on an unmaintained wrapper. The credible, "latest industry standard" approach — and the one WireGuard's own official apps use — is:

- **iOS:** `WireGuardKit` (Apple platforms library maintained under the WireGuard project) inside a **Network Extension (Packet Tunnel Provider)** app extension target.
- **Android:** `com.wireguard.android` (the official Android backend/`GoBackend`, same one shipped in the WireGuard Play Store app) inside a foreground **`VpnService`**.

You then write a **small first-party Expo Module** (Swift on iOS, Kotlin on Android) that wraps just the handful of calls the app actually needs — `connect(config)`, `disconnect()`, `getState()`, plus a state-change event stream — and ship it with an **Expo Config Plugin** that automates: adding the iOS Network Extension target and its entitlement, adding the Android `VpnService` declaration and foreground-service permissions, and wiring both into `expo prebuild`. This is a bounded, well-understood scope (a few hundred lines of native glue code, not a VPN client from scratch), and it means the actual cryptographic tunnel code is the same audited code WireGuard itself ships — you're only writing the bridge and lifecycle management.

### 2.3 Plain WireGuard peer, not an embedded Tailscale/Headscale client — and why

The Phase 13 plan uses Headscale (Tailscale-protocol) for the **hub and edge NVR fleet**, because those are always-on, fixed infrastructure that benefits from full mesh routing and DERP-relay NAT traversal. Embedding that *same* full coordination client inside a mobile app is a much heavier lift (it means bundling Tailscale's Go networking stack via mobile bindings, not just a WireGuard tunnel).

**Recommendation: the mobile app embeds a plain WireGuard client, not a full Tailscale-protocol client**, configured as a single peer pointed at the Hub's stable public WireGuard endpoint (the one deliberately-public UDP port from the Phase 13 plan). The Hub — which *is* a full Headscale/Tailscale node with subnet-routing into every site's tailnet — does the work of forwarding the mobile session's `AllowedIPs` into whichever site subnet that session is authorized to reach. This is simpler to embed, simpler to reason about, and matches how the hub-and-spoke live-view flow already works in §4.2 of the extension plan (the hub brokers the URL; for the mobile leg it also brokers the tunnel).

The one thing this design gives up is peer-to-peer NAT traversal directly from a mobile device to an edge NVR (DERP fallback) — traffic instead always routes hub → site, one hop, which is an entirely normal and reliable pattern for a hub-and-spoke commercial deployment and avoids asking a phone's WireGuard stack to do the harder job a full mesh client does.

### 2.4 Session-scoped keys, not a static VPN profile

- On first login on a device, the app generates a WireGuard keypair **on-device**, in the Expo Module (native), and stores the private key in Keychain/Keystore via `expo-secure-store` — **the private key never leaves the device, ever, not even to your own backend.**
- The app sends only the **public** key to a new hub endpoint (e.g. `POST /api/v1/mobile/vpn-session`), authenticated with the existing JWT. The hub registers that public key as a short-TTL Headscale peer, scoped (via ACL tags synced from RBAC, per §3.3 of the extension plan) to exactly the sites/cameras that user's role currently allows, and returns the peer config (hub endpoint, allowed IPs, keepalive) — never a static, long-lived `.conf` file.
- **Logout, session expiry, or a role/permission change immediately revokes the Headscale peer** via the same `acl_sync` mechanism already planned for the fleet. A stolen phone with the app installed but the user logged out has no active tunnel and no way to re-establish one without re-authenticating.

### 2.5 Tunnel lifecycle is UI-driven, not "always-on"

- Bring the tunnel up when the user opens **Live View** or **Playback** for a camera that resolves to a remote (non-hub-native) source, and when the app needs to fetch a **backup clip** (§4 of the extension plan) or resolve a **remote camera-onboarding** request (§4 below). Idle elsewhere in the app (dashboard summaries, settings, motion-alert list) doesn't need the tunnel up, since those calls go to the Hub's normal authenticated API which, per your existing design, still requires the tunnel only if you choose to route *all* API traffic through the overlay too — a reasonable simplification is to route **all** authenticated API calls through the tunnel once it's the app's only path to the Hub, and only gate *starting* the tunnel on "is any Hub-dependent screen active," tearing it down a short grace period (e.g. 2 minutes) after backgrounding.
- Do **not** ask for Android's system-level "Always-on VPN" designation — that changes system UI (persistent VPN key icon, lockdown mode prompts) and signals "this app tunnels all your traffic," which is the wrong mental model for a per-session, on-demand tunnel and adds friction in store review.
- **Push notifications never depend on the tunnel.** Motion/offline alerts (Phase 9/14 `notifier.py`) deliver over standard FCM/APNs with metadata only ("Motion at Front Door — tap to view"). Tapping the notification is what triggers the tunnel to come up just-in-time to fetch the actual clip — this keeps background battery/data use minimal while still giving near-real-time alerting.

### 2.6 App Store / Play Store considerations (plan for this, don't discover it late)

- iOS **Network Extension entitlement** is a manually-granted Apple Developer capability; request it early, it is not instant. Frame the app's purpose clearly in the review notes ("private connectivity to the customer's own surveillance devices," not a general-purpose consumer VPN) and complete the **Privacy Nutrition Label** accurately — VPN apps get closer review scrutiny on both stores.
- Android 14+ requires an explicit **foreground service type** declaration for a `VpnService`-backed connection and a persistent notification while the tunnel is active — treat this as a feature (it's honest, visible confirmation to the user that a secure tunnel is live) rather than a nuisance to hide.
- Budget calendar time for first submission specifically because of the VPN entitlement/review path — this is the single biggest schedule risk in the whole mobile plan, more than the OCR feature.

---

## 3. Feature: Add Camera by Photographing Its Serial Number

### 3.1 Concept

A field technician (or the customer themselves) points the phone at the printed label on the back/base of a new camera — the label that already carries a serial number, MAC address, and often a model code — and the app extracts that information automatically instead of someone typing a 16-character serial number and an RTSP URL by hand into a form. This is the same category of feature as a "scan to pair" flow, adapted to the reality that most CCTV camera labels are plain printed text plus, on many modern models, a QR code.

### 3.2 Two-tier capture strategy (QR first, OCR fallback)

**Tier 1 — QR code, if present.** Many current-generation IP cameras (several mainstream brands now do this) print a QR code on the label that already encodes structured connection info (serial, model, sometimes a device UID used by the vendor's own cloud P2P app). Scanning this, when present, is strictly better than reading printed text: it's a direct, error-free machine-readable payload. This tier uses `expo-camera`'s built-in `CameraView` barcode scanning — **notably, this specific capability works without any custom native module**, so it's the cheapest tier to build and the one to ship first.

**Tier 2 — OCR fallback for text-only labels.** When no QR is detected within a few seconds, the app switches to a live text-recognition overlay: React Native Vision Camera v4 with an ML Kit text-recognition frame-processor plugin, run on-device, throttled to a modest frame interval (processing every Nth frame is standard practice here for battery/thermal reasons — this doesn't need to run at full 30fps). Recognized text regions are outlined live on the preview so the user can see the scanner "notice" the label and hold steady, the same interaction pattern used by banking apps scanning card numbers.

Because the VPN feature already requires a custom Dev Client, adding this second tier costs nothing in terms of "can we still use Expo Go" — that door is already closed by §2 — so there's no reason to ship OCR as cloud-only to preserve Expo Go compatibility. **Recommendation: build both tiers, on-device, from the start.**

### 3.3 Parsing and matching, once text is captured

1. **Client-side heuristic extraction.** Run the raw OCR text through a small pattern library of known vendor serial-number/MAC formats (Hikvision, Dahua, CP Plus, Reolink, Uniview, TP-Link/Tapo, etc. — each vendor has a fairly consistent serial format, and MAC addresses are unambiguous `XX:XX:XX:XX:XX:XX`/`XXXXXXXXXXXX` patterns regardless of vendor). This narrows "a photo full of text" down to "this specific string is very likely the serial number, this one is the MAC."
2. **User confirmation, not silent trust.** Show the extracted fields (Serial, MAC, guessed model) in an editable form pre-filled from the scan, with a "doesn't look right? retake or edit" affordance. OCR on a smudged, glare-lit label will sometimes get one character wrong — a confirm step is cheap insurance against registering a camera under the wrong serial.
3. **Submit to the hub.** `POST /api/v1/cameras/onboard/scan` with the extracted fields (and, optionally, the captured photo itself for audit/support purposes). The hub:
   - Looks up the vendor from the serial/MAC prefix against a maintained `camera_model_registry` table (vendor → default ONVIF port, default RTSP path template, default credential pattern) so the technician doesn't have to know or type any of that.
   - Determines whether this onboarding is **local** (the requesting user's session is on the same network as the hub or an edge NVR the user is standing next to — inferred from the request coming in on the LAN rather than over the mobile VPN tunnel) or **remote**.

### 3.4 Local vs. remote onboarding paths

- **Local (technician standing at the hub or at a site with LAN access):** the hub immediately runs an ONVIF WS-Discovery sweep on that network, matches the discovered device's MAC against the scanned MAC, confirms the IP, and completes registration synchronously — the technician sees "Camera added" in seconds.
- **Remote (technician at a customer site behind an edge NVR, or the whole request arriving over the mobile VPN tunnel):** the hub creates a **pending camera** record and pushes it into that site's `nvr_node` via the existing `config_sync` channel from the extension plan's Phase 12 edge-agent. The edge-agent performs the ONVIF discovery locally at its next poll interval, matches the serial/MAC, and reports completion back to the hub. The technician's app shows "Registering… we'll notify you" and a **push notification** confirms success (or flags a mismatch — e.g. "found 3 unclaimed ONVIF devices on that network, please pick one" — if MAC matching is ambiguous, with a simple picker as the resolution UI).

### 3.5 Practical edge cases to design for up front

- **Duplicate serial:** if the scanned serial already exists in `survapp_camera_master`, surface that immediately rather than creating a second record, with a link to the existing camera's detail page.
- **Poor lighting/glare:** guide the user with a torch-toggle button and a framing overlay; don't silently fail — tell them what's wrong ("hold steady," "too dark, try the flashlight").
- **No connectivity at capture time:** if the technician is somewhere with no signal at all (common in basements/back rooms), cache the captured photo and extracted draft locally (`expo-file-system`) and queue the submission for the next time the app has connectivity, rather than losing the scan.
- **Manual fallback, always available:** a "type it in manually" link on the same screen for labels too worn to read and for any camera without a QR code, so the feature is a convenience layer over the existing manual flow, never a hard replacement for it.

### 3.6 Access control

Gate this entire feature behind the existing `camera.create` permission (already part of the multi-tenant RBAC model), and log every scan-based onboarding — including failed/ambiguous matches — to the existing audit log (`AuditLog` / `/audit` page), the same as any other camera-creation action. A photo-based add is still a privileged action; it should carry exactly the same authorization and traceability as filling out the form by hand always has.

---

## 4. Screen Inventory (Information Architecture)

| Screen | Purpose | Notes |
|---|---|---|
| Auth / Unlock | JWT login + biometric re-entry | `expo-local-authentication` gate on relaunch |
| Dashboard | Camera grid with health badges | Reuses Phase 9 `/health/cameras/` data |
| Live View | HLS/WebRTC playback, single or grid | Branches hub-native vs. edge-via-VPN per extension-plan §4.2 |
| Playback / DVR | Timeline scrubber, per-camera | Same timeline API as web, adapted UI |
| Motion Alerts | List + push-notification deep link target | Tapping a push opens straight to the relevant clip |
| Cameras | List/detail/edit | Entry point for both manual add and **Add Camera by Photo** |
| **Add Camera — Scan** | QR-first, OCR-fallback capture flow | §3 above |
| NVR Fleet (admin/installer role only) | Site health, provisioning, pending onboarding queue | Mirrors the web "NVR Fleet" page from the extension plan |
| Settings | Account, VPN/tunnel status indicator, notification prefs | Shows a plain-language tunnel status ("Secure connection: On"), not raw WireGuard internals |

---

## 5. Delivery Plan

### 5.1 Milestones
1. **M1 — App shell:** auth, dashboard, live view/playback against hub-native cameras only (no VPN yet) — validates the core product on top of the existing Phase 0–11 API without new native code.
2. **M2 — Embedded VPN:** Expo Module + Config Plugin for iOS Network Extension and Android VpnService, session-scoped key flow (§2.4), tunnel-lifecycle wiring (§2.5). Unlocks edge-camera live view/playback per the extension plan.
3. **M3 — Add Camera by Photo:** Tier 1 (QR via `expo-camera`) first as a fast win, then Tier 2 (Vision Camera v4 + ML Kit OCR), then the local/remote onboarding backend split (§3.4).
4. **M4 — Polish/commercial hardening:** push notifications end-to-end, offline queueing, Sentry wired up, design-system pass, store submission (start the iOS Network Extension entitlement request at the *start* of M2, not M4, given the review-time risk noted in §2.6).

### 5.2 What can ship as an OTA (EAS Update) vs. what needs a full store release
- **OTA-eligible:** JS/TS logic, UI, navigation, most of the scan-parsing heuristics in §3.3, API integration changes.
- **Requires a full binary release (store review):** anything touching the two native modules — VPN Expo Module changes, Vision Camera/ML Kit native dependency version bumps, Config Plugin changes, entitlement/permission changes. Plan native-module work in less-frequent, well-tested releases; keep everything else on the faster OTA cadence.

### 5.3 Testing
- **Unit/integration:** standard Jest + React Testing Library for JS logic (scan-parsing heuristics are very testable in isolation with a corpus of sample vendor label strings).
- **E2E:** Maestro or Detox for the critical flows (login → live view, scan → confirm → submit), run against Dev Client builds since Expo Go isn't in the picture here either.
- **Native module testing:** manual device-matrix testing for the VPN tunnel (multiple carriers/Wi-Fi/NAT conditions) and the OCR flow (multiple camera brands' real labels, varied lighting) — this class of bug rarely shows up in CI and needs a physical-device test pass before each native-module release.

---

## 6. Open Decisions

> [!IMPORTANT]
> **Q1 — Plain WireGuard peer (recommended, §2.3) vs. embedding a full Tailscale-protocol client on mobile.** The plain-peer approach is materially less native engineering and fits the hub-and-spoke model already chosen for the fleet; the cost is that mobile-to-edge traffic always takes one extra hop through the hub rather than a potential direct P2P path. Given mobile connections are inherently NAT'd and roaming anyway, that hop is not expected to be a meaningful latency cost in practice, but flag if very low-latency edge live-view (not just recorded playback) turns out to be a hard product requirement.

> [!IMPORTANT]
> **Q2 — OCR provider: on-device ML Kit only (recommended) vs. a cloud OCR fallback (e.g. for scripts/labels ML Kit struggles with).** On-device keeps the feature fully offline and avoids sending photos of hardware asset labels to a third party. Recommend shipping on-device only initially and revisiting a cloud fallback only if real-world recognition rates on your actual camera brand mix turn out to be poor.

> [!IMPORTANT]
> **Q3 — Who maintains the `camera_model_registry` (vendor serial-format → default ONVIF/RTSP template) table?** This needs an owner and a lightweight update process, since new camera models ship continuously. Recommend treating it as data, editable from an admin screen, not a hardcoded mapping in application code.

> [!WARNING]
> **iOS Network Extension entitlement lead time.** Start the Apple Developer entitlement request and prepare review-notes/privacy-label materials at the very start of the VPN milestone (M2), not near ship date — this has historically been the slowest, least predictable step in shipping any embedded-VPN iOS app.

> [!NOTE]
> This spec assumes the Phase 13 Headscale/DERP overlay from `sarvanetra_edge_vpn_extension_plan.md` is in place on the hub side; the mobile app's plain-WireGuard peer connects into that same overlay as a lightweight, hub-scoped participant rather than a full mesh member.