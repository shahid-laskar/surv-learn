#!/bin/sh
# kong/setup-kong-jwt.sh
#
# Provisions Kong:
#   1. A service + route for the FastAPI app, behind /api
#   2. A service + route for the HLS stream proxy (nginx_hls), behind /hls
#   3. JWT plugin enabled on both routes
#   4. A single Kong "consumer" representing the whole app backend, with a
#      JWT credential whose key/secret EXACTLY match KONG_JWT_ISSUER /
#      KONG_JWT_SECRET — these are the same values app/config.py uses to
#      sign tokens. This is the critical wiring point: Kong validates
#      tokens it didn't issue, by trusting that FastAPI signs them with
#      the same secret this consumer credential holds.
#
# Idempotent — safe to re-run; existing services/routes/plugins are skipped.

set -e
KONG_ADMIN="http://kong:8001"

echo "Waiting for Kong admin API..."
until curl -s -o /dev/null -w "%{http_code}" "$KONG_ADMIN/status" | grep -q "200"; do
  sleep 2
done
echo "Kong is up."

# ── 1. FastAPI service + route ──────────────────────────────────────────────
echo "Configuring FastAPI service..."
curl -s -X POST "$KONG_ADMIN/services" \
  -d "name=surv-api" \
  -d "url=http://app:8000" \
  > /dev/null || true

curl -s -X POST "$KONG_ADMIN/services/surv-api/routes" \
  -d "name=api-route" \
  -d "paths[]=/api" \
  -d "strip_path=false" \
  > /dev/null || true

# ── 2. HLS stream service + route ───────────────────────────────────────────
echo "Configuring HLS stream service..."
curl -s -X POST "$KONG_ADMIN/services" \
  -d "name=hls-stream" \
  -d "url=http://nginx_hls:80" \
  > /dev/null || true

curl -s -X POST "$KONG_ADMIN/services/hls-stream/routes" \
  -d "name=hls-route" \
  -d "paths[]=/hls" \
  -d "strip_path=false" \
  > /dev/null || true

# ── 3. JWT plugin ────────────────────────────────────────────────────────────
# Applied per-route. /api/v1/auth/login and /health stay open — Kong's JWT
# plugin has no per-path exclusion, so login must happen by hitting FastAPI's
# /docs or a route NOT behind this plugin. Simplest real-world fix: the
# frontend calls /api/v1/auth/login directly through Kong's api-route too,
# but the JWT plugin would block it before checking credentials, which is
# wrong for a login endpoint. To avoid this chicken-and-egg problem, the
# login route is exposed on a SEPARATE, unauthenticated Kong route below.
echo "Enabling JWT plugin on api-route..."
curl -s -X POST "$KONG_ADMIN/routes/api-route/plugins" \
  -d "name=jwt" \
  -d "config.claims_to_verify=exp" \
  > /dev/null || true

echo "Enabling JWT plugin on hls-route..."
curl -s -X POST "$KONG_ADMIN/routes/hls-route/plugins" \
  -d "name=jwt" \
  -d "config.claims_to_verify=exp" \
  -d "config.uri_param_names=token" \
  -d "config.cookie_names=jwt" \
  > /dev/null || true

# ── 3b. Unauthenticated login route ─────────────────────────────────────────
# A second route to the SAME FastAPI service, scoped only to /api/v1/auth/login
# and /health, with NO jwt plugin attached — this is how clients obtain a
# token in the first place.
echo "Configuring open auth route (login, no JWT required)..."
curl -s -X POST "$KONG_ADMIN/services/surv-api/routes" \
  -d "name=auth-open-route" \
  -d "paths[]=/api/v1/auth/login" \
  -d "paths[]=/api/v1/auth/stream" \
  -d "paths[]=/health" \
  -d "paths[]=/api/v1/health" \
  -d "strip_path=false" \
  > /dev/null || true

# ── 4. Consumer + JWT credential ────────────────────────────────────────────
# This consumer represents "the app backend" as a whole — FastAPI signs
# every token with this credential's secret, so any valid token issued by
# FastAPI is automatically trusted by Kong.
echo "Creating Kong consumer..."
curl -s -X POST "$KONG_ADMIN/consumers" \
  -d "username=sarvanetra-backend" \
  > /dev/null || true

echo "Provisioning JWT credential (key=$KONG_JWT_ISSUER)..."
EXISTING=$(curl -s "$KONG_ADMIN/consumers/sarvanetra-backend/jwt" | grep -c "\"key\":\"$KONG_JWT_ISSUER\"" || true)
if [ "$EXISTING" = "0" ]; then
  curl -s -X POST "$KONG_ADMIN/consumers/sarvanetra-backend/jwt" \
    -d "key=$KONG_JWT_ISSUER" \
    -d "algorithm=HS256" \
    -d "secret=$KONG_JWT_SECRET" \
    > /dev/null
  echo "JWT credential created."
else
  echo "JWT credential already exists, skipping."
fi

# ── 5. Rate limiting (commercial-grade default) ─────────────────────────────
echo "Enabling rate limiting (1000 req/min)..."
curl -s -X POST "$KONG_ADMIN/services/surv-api/plugins" \
  -d "name=rate-limiting" \
  -d "config.minute=1000" \
  -d "config.policy=local" \
  > /dev/null || true

# ── 6. CORS ──────────────────────────────────────────────────────────────────
# Kong sits in front of FastAPI, so the browser's preflight OPTIONS requests
# hit Kong first — FastAPI's CORSMiddleware never sees them. Kong must respond
# to preflights itself with the correct Access-Control-* headers.
echo "Enabling CORS plugin on surv-api service..."
curl -s -X POST "$KONG_ADMIN/services/surv-api/plugins" \
  -d "name=cors" \
  -d "config.origins=*" \
  -d "config.methods[]=GET" \
  -d "config.methods[]=POST" \
  -d "config.methods[]=PUT" \
  -d "config.methods[]=PATCH" \
  -d "config.methods[]=DELETE" \
  -d "config.methods[]=OPTIONS" \
  -d "config.methods[]=HEAD" \
  -d "config.headers[]=Authorization" \
  -d "config.headers[]=Content-Type" \
  -d "config.headers[]=Accept" \
  -d "config.headers[]=Origin" \
  -d "config.headers[]=X-Requested-With" \
  -d "config.exposed_headers[]=Authorization" \
  -d "config.credentials=false" \
  -d "config.max_age=3600" \
  -d "config.preflight_continue=false" \
  > /dev/null || true

echo "Kong configuration complete."
