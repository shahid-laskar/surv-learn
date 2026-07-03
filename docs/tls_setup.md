# TLS Certificate Setup Guide

The application expects wildcard TLS certificates for `*.bsnl.co.in` to securely serve HTTPS traffic via Kong and the frontend.

## 1. Directory Setup
Create a directory to hold your certificates on the host machine:
```bash
mkdir -p /opt/surv-learn/surv/certs
```

## 2. Place Certificates
Place the BSNL certificate and key in the `certs/` directory with the exact following names:
- `/opt/surv-learn/surv/certs/star_bsnl_co_in.crt`
- `/opt/surv-learn/surv/certs/star_bsnl_co_in.key`

## 3. Apply Configuration
The `docker-compose.yml` mounts this `certs/` directory into both the `frontend` container (Nginx) and the `kong-config` container.

When you start the stack:
```bash
docker compose down
docker compose up -d
```
1. **Frontend Nginx**: Will automatically bind to port 8443 and serve HTTPS using these certificates.
2. **Kong API Gateway**: The `kong-config` container runs the `setup-kong-jwt.sh` script, which automatically uploads the certificate to Kong's Admin API using the `/certs` directory mount.

## 4. Verification
Verify that both Kong and the frontend are serving the correct certificates:
```bash
curl -kvI https://sarvanetra.bsnl.co.in:8443
curl -kvI https://sarvanetra.bsnl.co.in:3443
```
