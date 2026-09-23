"""Unit tests for Kafka camera.status consumer logic."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../surv/workers")))

from status_consumer import process_status_event


def test_process_status_event_online_transition():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Initial state: camera is offline
    mock_cursor.fetchone.side_effect = [
        {"id": 1, "cam_id": "CAM01", "cam_name": "Front Gate", "is_online": False}, # lookup
        {"id": 100, "changed_at": datetime.now(timezone.utc) - timedelta(minutes=10)}, # previous log
    ]

    event = {
        "event_type": "camera_status",
        "camera": "CAM01",
        "status": "ready",
        "timestamp": 1700000000,
    }

    process_status_event(mock_conn, event)

    mock_conn.commit.assert_called()
    # Check that UPDATE survapp_camera_master was called with True
    update_called = any(
        "UPDATE survapp_camera_master" in str(call) and "SET is_online = %s" in str(call)
        for call in mock_cursor.execute.call_args_list
    )
    assert update_called is True


def test_process_status_event_offline_transition():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Initial state: camera is online
    mock_cursor.fetchone.side_effect = [
        {"id": 2, "cam_id": "CAM02", "cam_name": "Back Yard", "is_online": True},
        {"id": 105, "changed_at": datetime.now(timezone.utc) - timedelta(hours=1)},
    ]

    event = {
        "event_type": "camera_status",
        "camera": "CAM02",
        "status": "notReady",
        "timestamp": 1700000100,
    }

    with patch("status_consumer.send_camera_offline_alert") as mock_alert:
        process_status_event(mock_conn, event)
        mock_conn.commit.assert_called()
        mock_alert.assert_called_once_with(mock_conn, 2, "CAM02", "Back Yard")


def test_process_status_event_camera_not_found():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    event = {
        "event_type": "camera_status",
        "camera": "NON_EXISTENT",
        "status": "ready",
    }

    process_status_event(mock_conn, event)
    mock_conn.commit.assert_not_called()
