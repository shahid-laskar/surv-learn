> **Superseded:** See [sarvanetra_final_implementation_plan.md](sarvanetra_final_implementation_plan.md) for the authoritative implementation plan. This document is retained as historical reference.

# Sarvanetra — Phase 15 (Revised): VPN Remote Access for Admin & Customers
## Non-BSNL-Site Connectivity & Remote Management, Without Waiting for the Mobile App

*Builds directly on the completed Phase 12 (Edge NVR) and Phase 14 (WireGuard/Headscale Overlay) work. Mobile app (original Phases 15–17) is deferred — this plan delivers the remote-access outcome those phases were ultimately for, using the official Tailscale client instead of a custom embedded SDK, so it ships now rather than after mobile engineering.*

---

## 0. What This Plan Is Responding To

The commercial rollout plan (Phases 12–19) already:

- ✅ **Phase 12** — built the edge NVR appliance (`edge-agent`, local recording, heartbeat/config-sync to the hub)
- ✅ **Phase 14** — deployed Headscale + self-hosted DERP on the hub, giving every site NVR an encrypted, outbound-only overlay tunnel back to `100.64.0.1`

What's still missing is the **human** side of that overlay: a way for **admins** to manage the platform remotely, and a way for **customers** to view their own cameras remotely — both without exposing anything on the public internet, and both without waiting for the embedded-mobile-VPN work (Phases 15–17), which is now deferred.

The good news: **the infrastructure to do this already exists.** Headscale speaks the exact same protocol as the official Tailscale client apps (Windows, macOS, Linux, iOS, Android, and a browser-based client). Nothing new needs to be built at the network layer — this plan is about **who gets a peer identity, what they're allowed to reach, and how they get set up**, all sitting on top of the Phase 14 deployment you already have running.

---

## 1. Why the Official Tailscale App, Not a Custom Client

Since embedded mobile is deferred, the practical way to get a human onto the overlay today is the free, official Tailscale app, pointed at your self-hosted Headscale server instead of Tailscale's own SaaS coordination server (`tailscale up --login-server=https://vpn.sarvanetra.bsnl.co.in`). This is a first-class, supported way to use Headscale — it's not a workaround.

This gets you, with zero new native engineering:

- Clients for every platform an admin or customer might use — desktop (Windows/macOS/Linux) *and* the phone, today, without building or shipping anything of your own
- Automatic NAT traversal and reconnection (the same DERP relay from Phase 14 covers this)
- Either **pre-auth-key enrollment** (scan a link/QR, done — no login system needed) or, later, **OIDC-based login** (the user authenticates through a real identity provider and gets a peer tied to their identity, no manual key handling at all)
- All of this revocable centrally from Headscale, the same tool already managing your NVR fleet's peers

The tradeoff, and the reason the mobile SDK work still has value later: this app shows the customer a general-purpose "VPN connected" indicator and a second app icon, rather than a seamless single-app experience. That's an acceptable, even reasonable, interim state for launch — and nothing here needs to be thrown away when the embedded SDK ships; it plugs into the exact same ACL/tag model this plan sets up.

---

## 2. Two Personas, Two Access Profiles

### 2.1 Admin Remote Access

**Purpose:** manage the whole platform without being physically inside the BSNL VLAN — reach Kong's Admin API, Konga, MinIO console, Kafka UI, the NVR Fleet dashboard's backing API, and (for field diagnostics) SSH into edge boxes directly.

| | |
|---|---|
| Headscale tag | `group:admin` |
| ACL reach | `group:hub:*` (**all** internal admin ports — see §5 for which ones this newly makes it safe to un-expose publicly) **and** `group:nvr:*` (every site's overlay IP, all ports including SSH `:22` and MediaMTX's management API `:9997`) |
| Enrollment | Pre-auth key issued from a new admin-only screen, scoped to `group:admin`, delivered as a setup link/QR the admin scans once in the official Tailscale app |
| Expiry | Long-lived, tied to employment — revoked the moment the admin's Sarvanetra account is deactivated (see §4) |

Admins are deliberately **not** restricted the way customers are below — this tag is for your own operations staff.

### 2.2 Customer Remote Access

**Purpose:** let a customer view their own live/recorded footage and use the existing web dashboard from anywhere, with zero camera or NVR ever touching the public internet, and without requiring the customer to understand VPN configuration.

| | |
|---|---|
| Headscale tag | `group:customer:<customer_id>` (one tag per customer/org, reusing the existing multi-tenant `organization`/`customer` hierarchy) |
| ACL reach | **Only** the hub's Kong proxy port (the existing web app + API — nothing administrative) **and**, if that customer's cameras live behind an edge NVR, **only** that specific `nvr_node.overlay_ip`'s HLS port, exactly matching the existing stream-URL branching logic already built in Phase 14 (§14.4 of the commercial rollout plan) |
| Enrollment | See §3 — admin-provisioned to start, self-service as a fast-follow |
| Expiry | Sensible default (recommend 1 year, renewable) — **must** be revoked automatically the moment a customer's contract/account is deactivated |

This is the load-bearing difference from the admin profile: a customer's Tailscale peer must be unable to reach anything except their own dashboard and their own camera(s) — no other customer's NVR, no internal admin tooling, nothing else on the tailnet. Once a customer holds a general-purpose VPN client rather than a scoped in-app tunnel, **the ACL policy is the entire security boundary** — treated accordingly in §6.

### 2.3 Enrollment Options for Customers

**(a) Admin-provisioned, pre-auth key (ship this first).** From the existing Customers page in the multi-tenant frontend, an admin clicks "Enable Remote Access" → the hub calls Headscale to mint a pre-auth key tagged `group:customer:<id>` with an expiry → the resulting setup link/QR is shared with the customer however you already communicate with them (email, WhatsApp, a printed card at install time). The customer installs the official Tailscale app, scans it, done. **No new identity system required** — this reuses exactly the same pre-auth-key mechanism Phase 12 already uses to provision NVR boxes.

**(b) Self-service via OIDC login (fast-follow, not launch-blocking).** The customer logs into a "Remote Access" tab with their normal Sarvanetra credentials and can generate/revoke their own device's access without an admin in the loop. This is meaningfully more setup: **Headscale's OIDC support requires a real OpenID Connect identity provider** — your existing FastAPI JWT issuance is not itself an OIDC provider, so this path means standing up a lightweight self-hosted IdP (Authentik or Zitadel are the common self-hosted choices; either works, and Authentik/Zitadel both have Headscale integration guides) in front of Headscale, then wiring *that* IdP to check against your existing user table (or federate Sarvanetra accounts into it). Treat this as a distinct, optional milestone (§7, Step 7) — **(a) alone fully satisfies "customers can remotely view their cameras"** and should not wait on it.

---

## 3. What Changes in the Already-Built Phase 14 Pieces

Everything below **extends** files that already exist from Phase 14 — nothing here is a rebuild.

### 3.1 `headscale/acl.hcl` — extend the group model

The Phase 14 policy currently defines `group:hub`, `group:nvr`, and an unused `group:mobile`. Extend it with:

- `group:admin` — populated by the reconciliation job in §3.2, reaches everything (`group:hub:*` and `group:nvr:*`)
- `group:customer:<id>` — one dynamically-created group per customer/org with active remote access, reaching only that customer's slice of `group:hub` (the Kong proxy port specifically, not the whole hub) and that customer's specific NVR overlay IP(s) if applicable

`group:mobile` stays defined but empty while mobile is deferred — no need to remove it, since the embedded SDK work will populate it later without any ACL redesign.

> [!NOTE]
> Recent Headscale releases support a `tests` block in the policy file that asserts specific reachability/non-reachability rules and **rejects the policy write if a test fails** — this is directly useful here: write a test asserting a synthetic `group:customer:test` peer cannot reach `group:hub`'s admin ports or another customer's tag, and let Headscale itself enforce that invariant every time the policy is reloaded, rather than relying on manual review alone.

### 3.2 `app/services/acl_sync_service.py` — extend beyond mobile-session sync

Currently scoped (per the Phase 14 plan) to mobile-session peers. Extend its reconciliation loop to also handle:

1. **Admin sync:** every Sarvanetra user whose role is at admin tier gets (or keeps) a persistent `group:admin` Headscale tag; the moment that role is revoked or the account is deactivated, the tag/peer is removed.
2. **Customer sync:** every customer/org with remote access enabled gets a `group:customer:<id>` tag kept in sync with that customer's `nvr_camera_map`/`customer_site` assignment — if a customer's cameras move to a different NVR, or a site is decommissioned, the ACL scope updates automatically rather than silently going stale.

This is the same trigger model already planned for mobile (role change, permission change, camera-group change, user/customer assignment change) — just two more subjects reconciled through it.

### 3.3 New table: `vpn_peer` (extends `0006_edge_fleet`, no new migration file needed for the mobile-specific schema)

A persona-agnostic record of every issued Headscale peer/pre-auth key, deliberately independent of the mobile-specific `mobile_device` table planned for later:

```
vpn_peer
  id                SERIAL PRIMARY KEY
  subject_type      VARCHAR(20)      -- 'admin' | 'customer'
  subject_id         INTEGER          -- user_id (admin) or customer_id/org_id (customer)
  headscale_tag      VARCHAR(100)
  pre_auth_key_id    VARCHAR(100)
  device_label       VARCHAR(100)    -- optional, user-supplied ("Reception PC", "Owner's phone")
  issued_at          TIMESTAMPTZ
  expires_at         TIMESTAMPTZ
  revoked_at         TIMESTAMPTZ NULL
  last_seen          TIMESTAMPTZ NULL
```

### 3.4 New router: `app/routers/vpn.py`

```
POST   /api/v1/vpn/peers                 admin: issue a peer for a user, or for a customer/org
GET    /api/v1/vpn/peers                 admin: list all issued peers, status, last-seen
DELETE /api/v1/vpn/peers/{id}             admin: revoke immediately
GET    /api/v1/vpn/peers/me               any authenticated user: view their own active peer(s)
```
(`POST /api/v1/vpn/peers/me/setup-link` is deferred to §2.3(b) — self-service re-issue.)

### 3.5 Frontend additions

- **Admin — "VPN Access" page** (or a tab on the existing NVR Fleet / Settings page): table of every issued peer (admin and customer), online/offline status pulled from Headscale's node list, revoke button, and two "Issue Access" flows (one for staff, one for a selected customer/org) that render the resulting setup link as both a copyable link and a scannable QR code.
- **Customer-facing — "Remote Access" tab** (ships once §2.3(b) is built): shows the customer their own device(s) and lets them regenerate/revoke.

---

## 4. Lifecycle & Deprovisioning

- **Admin offboarding:** hook Headscale peer revocation into whatever already deactivates a staff account in the existing user management flow — a departing admin's tailnet access should end at the same moment their Sarvanetra login does, not on a separate schedule.
- **Customer churn:** hook the same `acl_sync_service` reconciliation into whatever already marks a customer/contract inactive — a churned customer's VPN peer should be revoked automatically, not left dangling because nobody remembered to click "revoke" on a separate screen.
- **Lost/stolen device:** the "VPN Access" admin screen's per-peer revoke button is the immediate remedy — revoking in Headscale takes effect on the peer's next handshake attempt, no coordination with the device itself required.

---

## 5. Hardening This Unlocks (Do This Once Admin Access Is Reliable)

Right now, several internal admin surfaces are reachable directly on the dev VM (Kong Admin `:8001`, Konga `:1337`, MinIO console `:9001`, Kafka UI `:8090`, and Headscale's own API `:8180`). Once admins have reliable overlay access, there's no remaining reason for any of these to accept connections from anywhere except the tailnet:

| Service | Current | Recommended |
|---|---|---|
| Kong Admin API | Host-bound port | Bind to `100.64.0.1` only, or firewall to accept only `100.64.0.0/10` sources |
| Konga | Host-bound port | Same — tailnet-only |
| MinIO Console | Host-bound port | Same — tailnet-only |
| Kafka UI | Host-bound port | Same — tailnet-only |
| Headscale API | Host-bound port | Same — tailnet-only (its OIDC callback endpoint, if §2.3(b) is built, is the one exception that needs to stay reachable pre-tunnel, since that's how a device *joins* the tailnet in the first place) |

This is a direct, concrete follow-on to Phase 11's hardening goals that wasn't achievable until now — Phase 11 could lock down CORS and TLS, but couldn't remove these admin ports from the network entirely without first giving admins another way in.

---

## 6. Security Notes Specific to This Plan

- **The ACL is now a Tier-1 control, not a nice-to-have.** A customer's device now holds a general-purpose Tailscale client rather than a scoped in-app tunnel — the only thing preventing that device from reaching more than its own dashboard is the ACL policy. Recommend the Headscale `tests` block (§3.1) run as part of any policy change, and ideally as a scheduled CI job against the live policy, not just at authoring time.
- **MagicDNS.** The Phase 14 config currently disables Headscale's MagicDNS (`magic_dns: false`). Recommend **enabling it** for this use case specifically — a customer or admin reaching `hub.sarvanetra.internal` in their browser is a materially better experience than copy-pasting `100.64.0.1`, and it costs nothing to turn on.
- **TLS for the in-tunnel browsing experience.** Phase 14 already requires a real certificate for `HEADSCALE_DOMAIN` (not self-signed) because Headscale itself needs it for client registration. Reuse that same domain/certificate for Kong's HTTPS listener too, so a customer opening the dashboard over the tunnel gets a clean padlock rather than the self-signed-cert warning Phase 11 accepted for the LAN-only case.
- **Least privilege by default.** New customer tags should default to "Kong proxy + own NVR only" with nothing else reachable — any broader access should be an explicit, logged exception, not a default.

---

## 7. Rollout Steps

1. **ACL & `acl_sync_service` extension** — add `group:admin` and `group:customer:*` handling (§3.1–3.2). No user-facing change yet.
2. **`vpn_peer` table + `app/routers/vpn.py`** (§3.3–3.4).
3. **Admin "VPN Access" UI** (§3.5) — issue real admin peers, pilot with 2–3 staff replacing their need to be physically on the BSNL VLAN.
4. **Customer admin-provisioned onboarding** (§2.3a) — pilot with 1–2 friendly customers before wider rollout.
5. **Tailnet-only hardening of internal admin ports** (§5) — only once Step 3 has proven admins can reliably reach what they need through the tunnel.
6. **MagicDNS + shared TLS cert for in-tunnel browsing** (§6).
7. *(Optional fast-follow, not launch-blocking)* **Self-service customer onboarding via OIDC** (§2.3b) — requires standing up a self-hosted OIDC IdP (Authentik or Zitadel) in front of Headscale.

---

## 8. Open Decisions

> [!IMPORTANT]
> **Which admin ports move to tailnet-only, and on what timeline?** Recommend all five listed in §5, but confirm none of them are still needed for a non-VPN'd break-glass access path (e.g. a physical console on the VM) before removing public exposure entirely.

> [!IMPORTANT]
> **Customer peer default expiry.** Proposed: 1 year, renewable by an admin (or self-service once §2.3b ships). Confirm this matches expected contract/renewal cadence.

> [!IMPORTANT]
> **OIDC provider choice, if/when Step 7 is pursued.** Authentik and Zitadel are the common self-hosted choices with documented Headscale integrations; this is a new piece of infrastructure to operate (backed up, monitored, patched) — not a configuration toggle. Confirm this is worth it before committing, versus simply continuing with admin-provisioned pre-auth keys indefinitely, which fully satisfies the stated requirement on their own.

> [!IMPORTANT]
> **SSH access to edge boxes for admins** — in scope for this rollout, or a later hardening task? The `group:admin` ACL already permits it (§2.1); what's undecided is whether the NVR Fleet page should surface a "connect" affordance for it now or this stays a CLI-only capability for now.

> [!NOTE]
> **Nothing here blocks the deferred mobile work.** The embedded WireGuard SDK plan (Phases 16–17, whenever resumed) plugs into the exact same Headscale instance, ACL model, and `acl_sync_service` this plan extends — it will add a `group:mobile` population step and its own peer-issuance flow, but the network, ACL grammar, and revocation model are already correct and won't need to change shape to accommodate it.

---

*This plan extends Phase 14 of the commercial rollout implementation plan and should be read alongside it, alongside the as-built status document, and alongside the (currently deferred) mobile app specification — nothing in those documents needs to change as a result of this plan; this fills the gap between "the overlay network exists" and "a human being can actually use it" without waiting on mobile engineering.*