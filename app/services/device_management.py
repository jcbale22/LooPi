# app/services/device_management.py

import uuid
from datetime import datetime, timedelta
from app.services.device_service import load_devices, save_devices


def audit_and_backfill_devices(default_license: str = "monthly"):
    """
    Ensures all devices have required fields:
    - auth_token
    - license_type
    - license_renewed_at
    - license_expires_at
    Only adds missing values; does not overwrite existing data.
    """
    now = datetime.utcnow()
    license_duration = timedelta(days=30) if default_license == "monthly" else timedelta(days=365)

    devices = load_devices()
    updated = False

    for device_id, device in devices.items():
        if "auth_token" not in device:
            device["auth_token"] = str(uuid.uuid4())
            updated = True

        if "license_type" not in device:
            device["license_type"] = default_license
            updated = True

        if "license_renewed_at" not in device:
            device["license_renewed_at"] = now.isoformat() + "Z"
            updated = True

        if "license_expires_at" not in device:
            device["license_expires_at"] = (now + license_duration).isoformat() + "Z"
            updated = True

    if updated:
        save_devices(devices)
        print("[✔] Devices updated with missing tokens and license fields.")
    else:
        print("[✓] All devices already have required fields.")


def rotate_auth_token(device_id: str) -> str | None:
    """
    Replaces the device's auth_token with a new one.
    Returns the new token if successful.
    """
    devices = load_devices()
    if device_id in devices:
        new_token = str(uuid.uuid4())
        devices[device_id]["auth_token"] = new_token
        save_devices(devices)
        return new_token
    return None


def renew_license(device_id: str, license_type: str = "monthly") -> bool:
    """
    Renews the license for a device.
    Updates the renewed_at and expires_at timestamps.
    """
    duration = timedelta(days=30) if license_type == "monthly" else timedelta(days=365)
    now = datetime.utcnow()

    devices = load_devices()
    if device_id in devices:
        devices[device_id]["license_type"] = license_type
        devices[device_id]["license_renewed_at"] = now.isoformat() + "Z"
        devices[device_id]["license_expires_at"] = (now + duration).isoformat() + "Z"
        save_devices(devices)
        return True
    return False
