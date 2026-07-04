# Sarvanetra — Internal Surveillance Platform on Isolated BSNL FTTH Network
**Technical Brief for Technical Manager**
*Classification: Internal — Not for Public Distribution*

---

## 1. Project Summary

**Sarvanetra** is a containerised, distributed CCTV management platform designed to ingest live feeds from IP cameras, store recordings, detect motion events, and surface everything through a web dashboard and REST API. The platform is built on open-source components — MediaMTX (media server), MinIO (object storage), Kafka (event pipeline), PostgreSQL, Redis, Nginx, and a Django/FastAPI application layer — orchestrated via Docker Compose.

**Core Constraint:** The platform must remain entirely within the BSNL intranet and must never be reachable from the public internet. This is achieved not through firewall rules alone, but through a dedicated VLAN at the optical access layer — physically and logically separated from the standard BSNL FTTH data VLAN.

---

## 2. Why a Separate VLAN — Not Just a Firewall

BSNL FTTH subscribers already ride on tagged VLANs from the ONT all the way to the BNG (Broadband Network Gateway). The standard data service (internet) uses VLANs in the 128–1499 range; VoIP uses VLAN 1830/1831/1849. Each service type has its own GEM port on the GPON link and its own forwarding context on the BNG.

Creating a **dedicated surveillance VLAN** means:

- Surveillance traffic never passes through the BNG's internet-facing routing context — it is terminated locally within the BSNL network or at an agreed aggregation point
- Even if the application server is misconfigured, there is no route to the public internet because the VLAN itself has no upstream default gateway pointing outside
- Camera streams (RTSP) and video storage traffic — which are high-bandwidth and latency-sensitive — stay on the local optical plant and do not consume internet quota
- The separation is enforced in hardware (OLT VLAN tagging, BNG context), not just software

---

## 3. Network Architecture

```
IP Cameras (RTSP/ONVIF)
        │
        │  LAN / PoE Switch (Camera VLAN)
        │
┌───────▼──────────────────────────────────────┐
│           ONT / HGU at Site                  │
│  LAN Port 1 → Internet (VLAN 100, DATA)      │
│  LAN Port 2 → Surveillance Server (VLAN 200) │◄── dedicated port/VLAN
└───────────────────┬──────────────────────────┘
                    │  GPON Fibre
                    │  GEM Port A → VLAN 100 (Data/Internet)
                    │  GEM Port B → VLAN 200 (Surveillance — no internet)
┌───────────────────▼──────────────────────────┐
│         OLT  (at BSNL Exchange / Cabinet)    │
│  Uplink tagged: VLAN 100 → BNG Internet ctx  │
│  Uplink tagged: VLAN 200 → BNG Intranet ctx  │
└───────────────────┬──────────────────────────┘
                    │
┌───────────────────▼──────────────────────────┐
│         BNG  (Broadband Network Gateway)      │
│  Context A: Internet — NAT, public IP pool    │
│  Context B: Surveillance Intranet — RFC 1918  │
│             private pool, NO default route    │
│             to internet                       │
└───────────────────┬──────────────────────────┘
                    │  MPLS / Metro Ethernet (BSNL backbone)
                    │
          ┌─────────▼──────────┐
          │  Sarvanetra Server │  (co-located or at another BSNL site)
          │  (Docker Compose)  │
          │  10.x.x.x/24      │
          └────────────────────┘
```

**Key point:** VLAN 200 (surveillance) traffic is terminated within the BSNL backbone. No packet on VLAN 200 ever reaches the internet routing table.

---

## 4. VLAN Design

| VLAN | Service | BSNL Element | BNG Context | Internet? |
|------|---------|-------------|-------------|-----------|
| 100 (example) | FTTH Data / Internet | OLT DATA port | Internet context | Yes |
| 1830/1831 | VoIP | OLT VoIP port | VOIP-IMS context | No (SIP only) |
| **200 (proposed)** | **Surveillance (Sarvanetra)** | **OLT — new GEM port** | **Intranet context** | **No** |

VLAN ID 200 is illustrative. The actual ID will be assigned by BSNL's NOC/RPoP team to avoid collision with existing service VLANs (128–1499 are in use for data; a value outside or a dedicated block agreed with BSNL is preferable, e.g. VLAN 500 or a range above 1500 if supported).

---

## 5. Configuration Requirements

### 5.1 At the OLT (BSNL Exchange / Cabinet)

Requires a **BSNL NOC/RPoP service request** (remedy docket). The BSNL JTO/NIC must:

1. Create a new VLAN (e.g. VLAN 200) on the OLT and tag it on the relevant uplink port toward the BNG
2. Create a new **GEM port** for the surveillance VLAN on the PON port serving the site's ONT
3. Bind the GEM port to VLAN 200 in the ONT's line profile (via OMCI)
4. Ensure VLAN 200 is **not** passed to the internet-facing uplink — only to the intranet/MPLS uplink

### 5.2 At the BNG

BSNL's NOC must create a new **subscriber context / VRF** for VLAN 200:

- Assign a private IP pool (e.g. `10.100.x.x/24`) with a DHCP scope
- Configure **no default route** to the internet in this context
- Allow only intra-BSNL routing (to the surveillance server and between authorised sites)
- Optionally: apply ACLs to permit only RTSP (554), HLS (8080/8888), and application API (8000) ports

### 5.3 At the ONT/HGU (Customer Premises)

The ONT must be configured (by BSNL technician or via OMCI remotely) to:

- Map **LAN Port 2 (or a dedicated Ethernet port)** to VLAN 200 as a tagged or untagged access port
- Keep LAN Port 1 on VLAN 100 (existing internet service — unchanged)
- Both VLANs travel on the same single fibre through separate GEM ports — no additional fibre required

### 5.4 At the Surveillance Server (Sarvanetra Host)

- Server NIC connected to ONT LAN Port 2 (VLAN 200)
- Assigned a private IP from BSNL's intranet DHCP pool (e.g. `10.100.1.10`)
- **No public IP. No NAT to internet.**
- Docker Compose stack runs as-is; all service ports (8000, 8554, 9000, etc.) are reachable only within VLAN 200

### 5.5 At Camera Sites (if multi-site)

Each site with cameras follows the same ONT dual-VLAN pattern. Cameras connect to the surveillance VLAN port on the ONT. The Sarvanetra server is reachable from all sites within VLAN 200 via BSNL's private backbone — without internet traversal.

---

## 6. Security Properties of This Design

| Property | How It Is Enforced |
|---|---|
| No internet exposure | VLAN 200 BNG context has no default route to public internet |
| Physical isolation | Separate GEM port on GPON — logically distinct from data traffic |
| Camera stream privacy | RTSP streams never leave BSNL's optical/backbone network |
| No NAT / no public IP | Server only holds an RFC 1918 address; no port forwarding possible |
| Layer 2 subscriber isolation | OLT prevents VLAN 200 subscribers from communicating with VLAN 100 subscribers |
| Access control | BNG ACLs can further restrict which ports/protocols are allowed within VLAN 200 |

---

## 7. What Sarvanetra Runs on This Network

Once the VLAN is provisioned, the Docker Compose stack is deployed on the surveillance server and operates entirely within `10.100.x.x`:

- **MediaMTX** ingests RTSP from cameras (all on VLAN 200 LAN)
- **MinIO** stores recordings locally on the server's disks
- **Kafka + workers** process motion events and camera status internally
- **Django/FastAPI** serves the management dashboard and REST API
- **Kong API Gateway** controls authenticated access to the dashboard — accessible only from within VLAN 200

Users access the system via a browser on a device connected to VLAN 200 (e.g. a dedicated workstation at a monitoring station, or via BSNL's intranet from an authorised office). No VPN to the internet is needed or allowed.

---

## 8. BSNL Coordination Checklist

The following must be formally requested from BSNL NOC/RPoP:

- [ ] Assign a dedicated VLAN ID for surveillance service (avoid clash with 128–1499 data range)
- [ ] Provision new GEM port on OLT for target ONT(s) mapped to surveillance VLAN
- [ ] Create intranet BNG context: private IP pool, DHCP, no internet default route
- [ ] Configure ONT LAN port mapping via OMCI (remote provisioning) or site visit
- [ ] Confirm VLAN tagged on OLT uplink toward intranet aggregation (not toward internet)
- [ ] Provide private IP range and DHCP server details to server administrator
- [ ] For multi-site: confirm VLAN 200 is routed across BSNL backbone between all site BNGs

---

## 9. Key Risks and Mitigations

| Risk | Mitigation |
|---|---|
| BSNL provisioning delay | Raise remedy docket early; get written confirmation of VLAN ID and timeline |
| ONT model does not support multi-VLAN / multi-service | Verify ONT model (Syrotech, Netlink, Huawei) supports dual GEM port / multi-service before requesting; replace ONT if needed |
| Accidental internet route in BNG | Request BSNL to run traceroute test from VLAN 200 context — should fail at BNG, not reach 8.8.8.8 |
| Camera RTSP on same VLAN as server | Correct by design — both on VLAN 200; no cross-VLAN routing to internet VLAN |
| Multi-site latency | BSNL backbone latency is typically <5 ms within a city; acceptable for RTSP and HLS |

---

*Prepared by: Development Team — Sarvanetra Project*
*For review and approval by Technical Manager before submission to BSNL NOC*