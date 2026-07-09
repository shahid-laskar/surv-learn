import os
import psycopg2
from datetime import datetime

DB_URL = "postgresql://surv:surv1234@10.44.0.209:5432/sarvanetra"

cameras = []
for site, port in [("01", 9554), ("02", 9555), ("03", 9556)]:
    for cam in [1, 2, 3]:
        cam_id = f"SIMCAM-SITE{site}-0{cam}"
        cameras.append((
            cam_id,
            f"Sim SITE{site} Cam 0{cam}",
            f"127.0.0.{int(site)}{cam}",
            8554,
            f"rtsp://10.44.0.209:{port}/{cam_id}",
            "admin", "admin", True, False, 7, datetime.now()
        ))

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
try:
    for c in cameras:
        cur.execute("""
            INSERT INTO survapp_camera_master 
            (cam_id, cam_name, cam_ip, cam_port, rtsp_url, onvif_username, onvif_password, is_active, motion_active, retention_days, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cam_id) DO NOTHING
        """, c)
    conn.commit()
    print("Simulated cameras registered successfully.")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
