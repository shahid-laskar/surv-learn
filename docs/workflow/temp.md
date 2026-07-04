docker compose exec postgres psql -U surv -d sarvanetra -c "
CREATE TABLE IF NOT EXISTS survapp_camera_master (
    id               SERIAL PRIMARY KEY,
    cam_id           VARCHAR(100) UNIQUE NOT NULL,
    cam_ip           VARCHAR(50)  NOT NULL,
    onvif_port       INTEGER      DEFAULT 80,
    onvif_username   VARCHAR(100) DEFAULT 'admin',
    onvif_password   VARCHAR(100) DEFAULT 'admin',
    is_active        BOOLEAN      DEFAULT true,
    is_online        BOOLEAN      DEFAULT false,
    motion_active    BOOLEAN      DEFAULT true,
    last_seen        TIMESTAMPTZ,
    created_at       TIMESTAMPTZ  DEFAULT NOW()
);

INSERT INTO survapp_camera_master
  (cam_id, cam_ip, onvif_port, onvif_username, onvif_password, is_active, motion_active)
VALUES
  ('CAMKRTVM00001', '10.44.0.219', 80, 'admin', 'admin', true, true)
ON CONFLICT (cam_id) DO NOTHING;

SELECT id, cam_id, cam_ip, is_active, motion_active FROM survapp_camera_master;
"

docker compose exec postgres psql -U surv -d sarvanetra -c "
CREATE TABLE IF NOT EXISTS survapp_motion_event (
    id           SERIAL PRIMARY KEY,
    camera_id    INTEGER      NOT NULL REFERENCES survapp_camera_master(id),
    motion_start TIMESTAMPTZ  NOT NULL,
    motion_end   TIMESTAMPTZ,
    is_active    BOOLEAN      DEFAULT true,
    created_at   TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_motion_event_camera_active
    ON survapp_motion_event(camera_id, is_active);
"

docker compose exec postgres psql -U surv -d sarvanetra -c "
SELECT id, camera_id, motion_start, motion_end, is_active
FROM survapp_motion_event
ORDER BY id DESC
LIMIT 10;
"