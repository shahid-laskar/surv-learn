-- Step 1: Ensure NVR nodes exist for all three simulated sites
INSERT INTO nvr_node (site_code, is_provisioned, created_at)
VALUES
  ('SITE01', false, NOW()),
  ('SITE02', false, NOW()),
  ('SITE03', false, NOW())
ON CONFLICT (site_code) DO NOTHING;

-- Step 2: Register simulated cameras (idempotent)
INSERT INTO survapp_camera_master
  (cam_id, cam_name, cam_ip, cam_port, rtsp_url, onvif_username, onvif_password,
   is_active, motion_active, retention_days, created_at)
VALUES
  ('SIMCAM-SITE01-01','Sim SITE01 Cam 01','127.0.0.11',8554,'rtsp://10.44.0.209:9554/SIMCAM-SITE01-01','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE01-02','Sim SITE01 Cam 02','127.0.0.12',8554,'rtsp://10.44.0.209:9554/SIMCAM-SITE01-02','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE01-03','Sim SITE01 Cam 03','127.0.0.13',8554,'rtsp://10.44.0.209:9554/SIMCAM-SITE01-03','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE02-01','Sim SITE02 Cam 01','127.0.0.21',8554,'rtsp://10.44.0.209:9555/SIMCAM-SITE02-01','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE02-02','Sim SITE02 Cam 02','127.0.0.22',8554,'rtsp://10.44.0.209:9555/SIMCAM-SITE02-02','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE02-03','Sim SITE02 Cam 03','127.0.0.23',8554,'rtsp://10.44.0.209:9555/SIMCAM-SITE02-03','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE03-01','Sim SITE03 Cam 01','127.0.0.31',8554,'rtsp://10.44.0.209:9556/SIMCAM-SITE03-01','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE03-02','Sim SITE03 Cam 02','127.0.0.32',8554,'rtsp://10.44.0.209:9556/SIMCAM-SITE03-02','admin','admin',true,false,7,NOW()),
  ('SIMCAM-SITE03-03','Sim SITE03 Cam 03','127.0.0.33',8554,'rtsp://10.44.0.209:9556/SIMCAM-SITE03-03','admin','admin',true,false,7,NOW())
ON CONFLICT (cam_id) DO NOTHING;

-- Step 3: Map cameras to their NVR nodes via nvr_camera_map
-- Uses CTEs to look up IDs without hard-coding them
WITH site01 AS (SELECT id FROM nvr_node WHERE site_code = 'SITE01'),
     site02 AS (SELECT id FROM nvr_node WHERE site_code = 'SITE02'),
     site03 AS (SELECT id FROM nvr_node WHERE site_code = 'SITE03')
INSERT INTO nvr_camera_map (nvr_node_id, camera_id)
SELECT site01.id, c.id FROM survapp_camera_master c, site01
  WHERE c.cam_id IN ('SIMCAM-SITE01-01','SIMCAM-SITE01-02','SIMCAM-SITE01-03')
UNION ALL
SELECT site02.id, c.id FROM survapp_camera_master c, site02
  WHERE c.cam_id IN ('SIMCAM-SITE02-01','SIMCAM-SITE02-02','SIMCAM-SITE02-03')
UNION ALL
SELECT site03.id, c.id FROM survapp_camera_master c, site03
  WHERE c.cam_id IN ('SIMCAM-SITE03-01','SIMCAM-SITE03-02','SIMCAM-SITE03-03')
ON CONFLICT DO NOTHING;
