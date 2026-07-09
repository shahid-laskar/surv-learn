# Sarvanetra Edge NVR

Portable site appliance stack: **MediaMTX** + **edge-agent**. Runs on a mini-PC or separate VM at the customer premises. Cameras stay on the local LAN; the agent syncs config and heartbeats to the Sarvanetra hub.

## Requirements

- Docker Engine + Compose v2
- Outbound HTTPS to the hub (`HUB_API_URL`)
- Cameras reachable via RTSP on the site LAN

## Deploy (LAN test against hub)

1. Provision an NVR in the hub UI (**NVR Fleet** → Add NVR). Copy `site_code` and `site_token`.
2. Copy and edit env:

```bash
cp .env.example .env
# Set SITE_CODE, SITE_TOKEN, HUB_API_URL=http://<hub-lan-ip>:8000/api/v1
```

3. Start:

```bash
docker compose up -d --build
```

4. On the hub, assign cameras to this NVR (Fleet API or UI). Within ~5 minutes the agent pulls RTSP paths into local MediaMTX.

## VPN overlay (optional)

```bash
# Set ENROLLMENT_PREAUTH_KEY and HEADSCALE_DOMAIN in .env
docker compose --profile vpn up -d --build
# Point HUB_API_URL at hub overlay IP, e.g. http://100.64.0.1:8000/api/v1
```

## Simulation

For multi-site testing with fake ffmpeg cameras, use the sibling **[edge-sim](../edge-sim/)** package.

## Layout

```
edge-nvr/
├── docker-compose.yml
├── mediamtx/mediamtx.yml
└── edge-agent/          # Python agent (heartbeat, config, motion, retention, backup)
```
