# SARVANETRA — Complete REST API Contract Specification
**Document ID:** `API-SPEC-001`  
**Classification:** Open API & Microservice Contract  
**Version:** 2.0 (Post-Stabilization Baseline)  
**Base Path:** `/api/v1`  
**Authentication Schemes:**
1. `Bearer <JWT>`: Standard user session token issued by `/api/v1/auth/token`.
2. `X-Site-Token <Token>`: Edge NVR mutual authentication header for fleet endpoints.

---

## 1. Authentication & Session Services (`/auth`)

### 1.1 Obtain Access Token (Login)
* **Endpoint:** `POST /api/v1/auth/token`
* **Auth:** None (Public / Basic Credentials)
* **Request:** `OAuth2PasswordRequestForm` (`username`, `password`)
* **Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer",
  "expires_in": 28800
}
```
* **Error:** `401 Unauthorized` (`Invalid credentials`)

### 1.2 User Profile & Claims
* **Endpoint:** `GET /api/v1/auth/me`
* **Auth:** Bearer JWT
* **Response:** `200 OK`
```json
{
  "id": 1,
  "username": "admin",
  "user_type": "EMPLOYEE",
  "roles": ["SUPER_ADMIN"],
  "permissions": ["camera.view", "camera.manage", "parking.view", "parking.manage", "anpr.view", "anpr.manage", "incident.manage", "evidence.manage"]
}
```

---

## 2. Camera Management Services (`/cameras`)

### 2.1 List Accessible Cameras
* **Endpoint:** `GET /api/v1/cameras`
* **Auth:** Bearer JWT
* **Permission:** `camera.view` (scoped by organizational hierarchy)
* **Response:** `200 OK`
```json
[
  {
    "id": 1,
    "cam_id": "CAMKRTVM0001",
    "cam_name": "Nilakkal Entry Gate 1",
    "cam_ip": "192.168.1.101",
    "rtsp_url": "rtsp://admin:pass@192.168.1.101:554/ch0",
    "is_online": true,
    "is_active": true,
    "customer_site_id": 1
  }
]
```

### 2.2 Register Camera
* **Endpoint:** `POST /api/v1/cameras`
* **Auth:** Bearer JWT
* **Permission:** `camera.manage`
* **Request Body:**
```json
{
  "cam_id": "CAM_NILAKKAL_10",
  "cam_name": "Nilakkal Ground 10 North",
  "cam_ip": "192.168.10.10",
  "stream_protocol": "RTSP",
  "customer_site_id": 1
}
```
* **Response:** `201 Created`

### 2.3 Deactivate Camera
* **Endpoint:** `DELETE /api/v1/cameras/{cam_id}`
* **Auth:** Bearer JWT
* **Permission:** `camera.manage`
* **Response:** `204 No Content` (removes route from MediaMTX and soft-deactivates DB row)

---

## 3. Video Playback & Timeline Services (`/recordings`)

### 3.1 Get Camera Timeline
* **Endpoint:** `GET /api/v1/recordings/timeline`
* **Auth:** Bearer JWT
* **Params:** `cam_id` (string), `start_time` (ISO8601), `end_time` (ISO8601)
* **Response:** `200 OK`
```json
{
  "camera_id": "CAMKRTVM0001",
  "segments": [
    {
      "segment_id": 1052,
      "start_time": "2026-09-23T06:00:00Z",
      "end_time": "2026-09-23T06:01:00Z",
      "duration_seconds": 60,
      "object_key": "CAMKRTVM0001/2026/09/23/06-00-00.mp4"
    }
  ]
}
```

### 3.2 Presigned Segment Download URL
* **Endpoint:** `GET /api/v1/recordings/download-url`
* **Auth:** Bearer JWT
* **Params:** `object_key` (string)
* **Response:** `200 OK`
```json
{
  "download_url": "https://storage.sarvanetra.internal/recordings/CAM01/...?X-Amz-Signature=..."
}
```

---

## 4. Edge Fleet Ingestion Services (`/fleet`)

### 4.1 Edge NVR Heartbeat
* **Endpoint:** `POST /api/v1/fleet/heartbeat`
* **Auth:** Header `X-Site-Token: <site_token>` (Kong Edge Route)
* **Request Body:**
```json
{
  "site_code": "SITE01",
  "cameras_online": 8,
  "cameras_total": 8,
  "disk_free_gb": 420.5,
  "cpu_load": 12.4
}
```
* **Response:** `200 OK` (`{"status": "acknowledged", "config_version": 4}`)

---

## 5. Smart Parking Management Services (`/parking`)

### 5.1 List Parking Zones & Real-Time Occupancy
* **Endpoint:** `GET /api/v1/parking/zones`
* **Auth:** Bearer JWT
* **Response:** `200 OK`
```json
[
  {
    "id": 1,
    "zone_code": "GROUND_01",
    "name": "Nilakkal Ground 1 (LMV)",
    "vehicle_type": "LMV",
    "total_capacity": 450,
    "current_occupancy": 120,
    "available_slots": 330,
    "is_active": true
  }
]
```

### 5.2 Vehicle Entry & Slot Allocation
* **Endpoint:** `POST /api/v1/parking/entry`
* **Auth:** Bearer JWT (`parking.manage`)
* **Request Body:**
```json
{
  "vehicle_number": "KL01AB1234",
  "vehicle_type": "LMV",
  "customer_site_id": 1,
  "lane_id": 1
}
```
* **Response:** `201 Created`
```json
{
  "session_id": 84,
  "vehicle_number": "KL01AB1234",
  "allocated_zone_code": "GROUND_01",
  "zone_name": "Nilakkal Ground 1 (LMV)",
  "entry_slip_number": "SLIP-KL01AB1234-1790150400",
  "entry_time": "2026-09-23T07:15:00Z"
}
```

### 5.3 Vehicle Exit
* **Endpoint:** `POST /api/v1/parking/exit`
* **Auth:** Bearer JWT
* **Request Body:**
```json
{
  "entry_slip_number": "SLIP-KL01AB1234-1790150400",
  "fee_collected": 50.0
}
```
* **Response:** `200 OK` (`{"status": "COMPLETED", "duration_minutes": 185, "fee_amount": 50.0}`)

---

## 6. ANPR & Watchlist Services (`/anpr`)

### 6.1 Ingest ANPR Detection Event
* **Endpoint:** `POST /api/v1/anpr/events`
* **Auth:** Bearer JWT or `X-Site-Token`
* **Request Body:**
```json
{
  "plate": "KL07BH9999",
  "confidence": 0.96,
  "vehicle_type": "CAR",
  "vehicle_color": "white",
  "camera_id": 1,
  "customer_site_id": 1,
  "captured_at": "2026-09-23T07:30:00Z"
}
```
* **Response:** `201 Created`
```json
{
  "id": 1420,
  "plate_number": "KL07BH9999",
  "normalized_plate": "KL07BH9999",
  "alerts_triggered": [
    {
      "alert_id": 12,
      "category": "WANTED",
      "severity": "CRITICAL",
      "reason": "Robbery suspect vehicle (Pathanamthitta)"
    }
  ]
}
```

### 6.2 Fuzzy License Plate Search
* **Endpoint:** `GET /api/v1/anpr/search`
* **Auth:** Bearer JWT (`anpr.view`)
* **Params:** `plate` (string), `fuzzy` (bool, default true), `limit` (int)
* **Response:** `200 OK` (uses PostgreSQL `pg_trgm` GIN index for approximate OCR tolerance)

---

## 7. Incident Management & Forensic Evidence (`/incidents`, `/evidence`)

### 7.1 Create Incident
* **Endpoint:** `POST /api/v1/incidents`
* **Auth:** Bearer JWT (`incident.manage`)
* **Request Body:**
```json
{
  "title": "Stolen Vehicle Sighting - Nilakkal Gate 1",
  "severity": "HIGH",
  "category": "SECURITY",
  "source_type": "ANPR_WATCHLIST",
  "customer_site_id": 1
}
```
* **Response:** `201 Created` (`incident_number`: `INC-2026-0001`)

### 7.2 Export Cryptographically Sealed Evidence Package
* **Endpoint:** `POST /api/v1/evidence/export`
* **Auth:** Bearer JWT (`evidence.manage`)
* **Request Body:**
```json
{
  "incident_id": 1,
  "title": "Forensic Video & ANPR Capture Package",
  "camera_ids": [1],
  "start_time": "2026-09-23T07:25:00Z",
  "end_time": "2026-09-23T07:35:00Z",
  "include_anpr": true
}
```
* **Response:** `201 Created`
```json
{
  "package_id": 4,
  "manifest_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
  "verification_status": "SEALED_VALID",
  "manifest": {
    "package_id": 4,
    "incident_id": 1,
    "sealed_at": "2026-09-23T07:45:00Z",
    "video_segments": ["CAMKRTVM0001/2026/09/23/07-30-00.mp4"]
  }
}
```
