# Dynamic Camera Registration with MediaMTX

Currently, cameras are statically configured in `mediamtx.yml`, requiring a restart to add or remove streams. We will implement dynamic configuration via MediaMTX's REST API (`:9997`).

## Open Questions
- If `rtsp_url` is not set in the database, what should the fallback format be? (e.g., `rtsp://[user]:[pass]@[ip]:554/unicaststream/2`)
- Should we completely remove `CAMKRTVM0001` from `mediamtx.yml` now, or leave it as a static fallback?

## Proposed Changes

### MediaMTX Service
#### [NEW] [mediamtx_client.py](file:///opt/surv-learn/surv/app/services/mediamtx_client.py)
Create a new service utilizing `httpx` to interact with the MediaMTX API.
- `add_camera(cam_id, rtsp_url)`: Sends a `POST` to `/v3/config/paths/add/{cam_id}`.
- `remove_camera(cam_id)`: Sends a `DELETE` to `/v3/config/paths/delete/{cam_id}`.
- `sync_cameras(cameras)`: Takes a list of active cameras from the DB and adds them.

### Application Lifecycle
#### [MODIFY] [main.py](file:///opt/surv-learn/surv/app/main.py)
Update the FastAPI `lifespan` event to:
- Query all active cameras from the database on startup.
- Call `mediamtx_client.sync_cameras()` to ensure MediaMTX immediately starts streaming them upon backend startup.

### Camera Routes
#### [MODIFY] [cameras.py](file:///opt/surv-learn/surv/app/routers/cameras.py)
Hook into the CRUD operations:
- `create_camera`: If the camera is active, call `mediamtx_client.add_camera()`.
- `update_camera`: If `rtsp_url` or `is_active` changes, update MediaMTX accordingly (add or remove).
- `deactivate_camera`: Call `mediamtx_client.remove_camera()`.

## Verification Plan
### Automated Tests
N/A

### Manual Verification
1. Verify the backend starts up successfully and syncs the existing camera.
2. Create a dummy camera via the API and verify that MediaMTX attempts to stream it (visible in `nginx_hls` or `mediamtx` logs).
3. Deactivate the dummy camera and verify MediaMTX stops streaming it.
