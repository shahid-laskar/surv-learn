#!/usr/bin/env python3

import os
import sys
import json
import logging
import psycopg2
import subprocess
from datetime import datetime, timedelta
from minio import Minio

# Early debug logging
DEBUG_LOG = "/tmp/upload_debug.log"

def debug_log(message):
    """Write debug info to a simple log file"""
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(f"{datetime.now()}: {message}\n")
    except Exception as e:
        print(f"Debug log failed: {e}", file=sys.stderr)

# Log script start with environment variables (not command line args)
debug_log(f"Script started")
debug_log(f"MTX_PATH: {os.getenv('MTX_PATH', 'NOT_SET')}")
debug_log(f"MTX_SEGMENT_PATH: {os.getenv('MTX_SEGMENT_PATH', 'NOT_SET')}")
debug_log(f"MTX_SEGMENT_DURATION: {os.getenv('MTX_SEGMENT_DURATION', 'NOT_SET')}")

try:
    import json
    import logging
    import psycopg2
    import subprocess
    from datetime import datetime, timedelta
    from minio import Minio
    debug_log("All imports successful")
except ImportError as e:
    debug_log(f"Import error: {e}")
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)

# ---------------- CONFIG ----------------
CONFIG = {
    "MINIO_ENDPOINT": os.getenv("MINIO_ENDPOINT", "minio:9000"),
    "MINIO_ACCESS_KEY": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    "MINIO_SECRET_KEY": os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
    "MINIO_USE_SSL": os.getenv("MINIO_USE_SSL", "false").lower() == "true",
    "DEFAULT_BUCKET": os.getenv("DEFAULT_BUCKET", "cctv-recordings"),
    "DATABASE_URL": os.getenv("DATABASE_URL", "postgres://bsnlkl_itcell:Itcell123*@192.168.210.20/sarvanetra"),
    "LOG_FILE": os.getenv("LOG_FILE", "/recordings/logs/upload.log"),
}

debug_log(f"Config loaded: {CONFIG}")

# Setup logging
try:
    os.makedirs(os.path.dirname(CONFIG["LOG_FILE"]), exist_ok=True)
    logging.basicConfig(
        filename=CONFIG["LOG_FILE"], 
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s"
    )
    # Also log to console for debugging
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)
    
    debug_log("Logging setup successful")
    logging.info("Upload script started")
except Exception as e:
    debug_log(f"Logging setup failed: {e}")
    print(f"Logging setup failed: {e}", file=sys.stderr)

# MinIO client
try:
    minio_client = Minio(
        CONFIG["MINIO_ENDPOINT"],
        access_key=CONFIG["MINIO_ACCESS_KEY"],
        secret_key=CONFIG["MINIO_SECRET_KEY"],
        secure=CONFIG["MINIO_USE_SSL"]
    )
    debug_log("MinIO client created")
    logging.info(f"MinIO client connected to: {CONFIG['MINIO_ENDPOINT']}")
except Exception as e:
    debug_log(f"MinIO client creation failed: {e}")
    logging.error(f"MinIO client creation failed: {e}")
    sys.exit(1)

# ---------------- HELPERS ----------------
def parse_recording_path(file_path):
    """
    Parse recording path: /recordings/CAMKRLTVM00003/2025/09/22/11-01-26-983631-live/CAMKRLTVM00003.mp4
    Returns: (camera_id, start_time)
    """
    parts = file_path.strip("/").split("/")
    logging.info(f"Parsing path parts: {parts}")
    
    if len(parts) < 6:
        raise ValueError(f"Invalid file path format: {file_path}")

    # Find the recordings index
    try:
        recordings_idx = parts.index("recordings")
        start_idx = recordings_idx + 1
    except ValueError:
        # If "recordings" not found, assume it starts from index 0
        start_idx = 0
    
    # Find year by looking for 4-digit number
    year_idx = None
    for i, part in enumerate(parts):
        if part.isdigit() and len(part) == 4 and 2000 <= int(part) <= 2100:
            year_idx = i
            break
    
    if year_idx is None:
        raise ValueError(f"Cannot find year in path: {file_path}")
    
    # Camera path is everything between recordings and year
    camera_parts = parts[start_idx:year_idx]
    camera_id = "/".join(camera_parts)  # This will be "CAMKRLTVM00003"
    
    year = parts[year_idx]
    month = parts[year_idx + 1]
    day = parts[year_idx + 2]
    timestamp_dir = parts[year_idx + 3]  # This contains the actual timestamp: "11-01-26-983631-live"
    
    logging.info(f"Extracted: camera_id={camera_id}, year={year}, month={month}, day={day}, timestamp_dir={timestamp_dir}")
    
    # Parse timestamp from directory name: "11-01-26-983631-live"
    # Remove the "-live" suffix if present
    if timestamp_dir.endswith('-live'):
        time_part = timestamp_dir[:-5]  # Remove "-live"
    else:
        time_part = timestamp_dir
    
    logging.info(f"Time part: {time_part}")
    
    time_parts = time_part.split("-")
    logging.info(f"Time parts: {time_parts}")
    
    if len(time_parts) != 4:
        raise ValueError(f"Expected 4 time parts (HH-MM-SS-microseconds), got {len(time_parts)}: {time_parts}")
    
    hh, mm, ss, micros = time_parts
    start_time = datetime(
        int(year), int(month), int(day),
        int(hh), int(mm), int(ss),
        int(micros) // 1000  # convert microsecond string to microseconds
    )

    return camera_id, start_time


def get_video_duration(file_path):
    """Use ffprobe to get video duration in seconds (float)."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", file_path
    ]
    logging.info(f"Running ffprobe: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"ffprobe stderr: {result.stderr}")
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])
    logging.info(f"Video duration: {duration} seconds")
    return duration


def get_camera_db_id(conn, camera_id):
    """Lookup camera id in database."""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM survapp_camera_master WHERE cam_id = %s LIMIT 1", (camera_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Camera not found in DB: {camera_id}")
        return row[0]


def upload_to_minio(local_path, bucket_name, object_name):
    """Upload file to MinIO, create bucket if missing."""
    try:
        found = minio_client.bucket_exists(bucket_name)
        if not found:
            minio_client.make_bucket(bucket_name)
            logging.info(f"Created bucket: {bucket_name}")
        else:
            logging.info(f"Using existing bucket: {bucket_name}")

        minio_client.fput_object(bucket_name, object_name, local_path, content_type="video/mp4")
        logging.info(f"Uploaded to MinIO: {bucket_name}/{object_name}")
    except Exception as e:
        logging.error(f"MinIO upload failed: {e}")
        raise


def save_to_database(conn, segment):
    """Insert video segment into Postgres."""
    query = """
        INSERT INTO survapp_videosegment (
            camera_id, start_time, end_time, duration,
            file_path, file_size, minio_bucket, created_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    with conn.cursor() as cur:
        cur.execute(query, (
            segment["camera_id"],
            segment["start_time"],
            segment["end_time"],
            segment["duration"],
            segment["file_path"],
            segment["file_size"],
            segment["bucket"],
            segment["created_at"]
        ))
    conn.commit()
    logging.info("Database record saved successfully")


# ---------------- MAIN ----------------
def main():
    debug_log("Main function started")
    
    # Get values from environment variables (like your shell script does)
    camera_path = os.getenv('MTX_PATH')
    file_path = os.getenv('MTX_SEGMENT_PATH')
    segment_duration = os.getenv('MTX_SEGMENT_DURATION')
    
    debug_log(f"Environment variables - Path: {camera_path}, File: {file_path}, Duration: {segment_duration}")
    
    if not camera_path:
        error_msg = "MTX_PATH environment variable not set"
        debug_log(error_msg)
        logging.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    if not file_path:
        error_msg = "MTX_SEGMENT_PATH environment variable not set"
        debug_log(error_msg)
        logging.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    logging.info(f"Processing upload: camera_path={camera_path}, file_path={file_path}")
    debug_log(f"Processing: {camera_path}, {file_path}")

    if not os.path.exists(file_path):
        error_msg = f"File not found: {file_path}"
        logging.error(error_msg)
        debug_log(error_msg)
        sys.exit(1)

    try:
        # Parse path
        camera_id, start_time = parse_recording_path(file_path)
        logging.info(f"Parsed: camera_id={camera_id}, start_time={start_time}")

        # Get real duration (or use the duration from MediaMTX if available)
        if segment_duration:
            try:
                duration = float(segment_duration)
                logging.info(f"Using MediaMTX provided duration: {duration} seconds")
            except ValueError:
                duration = get_video_duration(file_path)
        else:
            duration = get_video_duration(file_path)
        
        end_time = start_time + timedelta(seconds=duration)

        # File info
        file_size = os.path.getsize(file_path)
        logging.info(f"File size: {file_size} bytes")

        # Object name for MinIO
        timestamp = start_time.strftime("%Y-%m-%d_%H-%M-%S")
        object_name = f"{camera_id}/{camera_id}_{timestamp}.mp4"
        logging.info(f"MinIO object name: {object_name}")

        # Database connection
        logging.info("Connecting to database...")
        conn = psycopg2.connect(CONFIG["DATABASE_URL"])

        # Lookup camera
        db_camera_id = get_camera_db_id(conn, camera_id)
        logging.info(f"Database camera ID: {db_camera_id}")

        # Upload to MinIO
        logging.info("Starting MinIO upload...")
        upload_to_minio(file_path, CONFIG["DEFAULT_BUCKET"], object_name)

        # Save DB record
        segment = {
            "camera_id": db_camera_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "file_path": object_name,
            "file_size": file_size,
            "bucket": CONFIG["DEFAULT_BUCKET"],
            "created_at": datetime.utcnow()
        }
        save_to_database(conn, segment)
        conn.close()

        success_msg = f"Successfully processed: {object_name}"
        logging.info(success_msg)
        debug_log(success_msg)

    except Exception as e:
        error_msg = f"Failed to process segment: {e}"
        logging.error(error_msg)
        debug_log(error_msg)
        debug_log(f"Exception type: {type(e).__name__}")
        import traceback
        debug_log(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        debug_log(f"Unhandled exception in main: {e}")
        import traceback
        debug_log(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)