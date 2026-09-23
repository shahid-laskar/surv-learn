"""
surv/app/tests/test_evidence.py
Unit tests for Evidence Packaging and Cryptographic Verification:
Generates certified export packages, validates SHA-256 manifests,
and rigorously verifies tamper-detection against modified archives.
"""

import os
import tempfile
import zipfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.evidence import EvidenceExportRequest
from app.services.evidence_service import EvidenceService, calculate_sha256


@pytest.mark.asyncio
async def test_create_and_verify_evidence_package_untampered():
    db = AsyncMock()
    db.add = MagicMock()

    with tempfile.TemporaryDirectory() as temp_dir:
        req = EvidenceExportRequest(
            title="Sabarimala Perimeter Breach Incident",
            description="Exported for Kerala Police Pathanamthitta",
            incident_id=1,
            camera_id=10,
        )

        pkg = await EvidenceService.create_evidence_package(
            db, req, user_id=1, output_base_dir=temp_dir
        )

        assert os.path.isfile(pkg.file_path)
        assert pkg.file_path.endswith(".zip")
        assert len(pkg.sha256_hash) == 64
        assert pkg.file_size_bytes > 0

        # Verify integrity of untampered package
        result = EvidenceService.verify_evidence_package(pkg.file_path)
        assert result.is_valid is True
        assert result.tamper_detected is False
        assert len(result.mismatched_files) == 0
        assert result.calculated_manifest_hash == result.stored_manifest_hash


@pytest.mark.asyncio
async def test_detect_tampered_payload_file():
    db = AsyncMock()
    db.add = MagicMock()

    with tempfile.TemporaryDirectory() as temp_dir:
        req = EvidenceExportRequest(title="Tamper Test Incident")
        pkg = await EvidenceService.create_evidence_package(
            db, req, user_id=1, output_base_dir=temp_dir
        )

        # Deliberately modify media/incident_clip_01.mp4 inside the zip
        tampered_zip = os.path.join(temp_dir, "tampered_pkg.zip")

        with zipfile.ZipFile(pkg.file_path, "r") as zin:
            with zipfile.ZipFile(tampered_zip, "w") as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if "incident_clip_01.mp4" in item.filename:
                        # Tamper with video payload bytes
                        data = data + b"MALICIOUS_UNAUTHORIZED_MUTATION_BYTES"
                    zout.writestr(item, data)

        # Verification must detect the tampering
        result = EvidenceService.verify_evidence_package(tampered_zip)
        assert result.is_valid is False
        assert result.tamper_detected is True
        assert any("incident_clip_01.mp4" in f for f in result.mismatched_files)


@pytest.mark.asyncio
async def test_detect_tampered_manifest_seal():
    db = AsyncMock()
    db.add = MagicMock()

    with tempfile.TemporaryDirectory() as temp_dir:
        req = EvidenceExportRequest(title="Seal Tamper Test")
        pkg = await EvidenceService.create_evidence_package(
            db, req, user_id=1, output_base_dir=temp_dir
        )

        # Deliberately modify manifest.json without updating manifest.sha256
        tampered_zip = os.path.join(temp_dir, "seal_tampered_pkg.zip")

        with zipfile.ZipFile(pkg.file_path, "r") as zin:
            with zipfile.ZipFile(tampered_zip, "w") as zout:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "manifest.json":
                        data = data.replace(b"EVD-", b"EVX-")
                    zout.writestr(item, data)

        # Verification must detect seal mismatch
        result = EvidenceService.verify_evidence_package(tampered_zip)
        assert result.is_valid is False
        assert result.tamper_detected is True
        assert any("SEAL_TAMPERED" in f for f in result.mismatched_files)
