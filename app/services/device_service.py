# app/services/device_service.py

import json
import uuid
from pathlib import Path
from datetime import datetime

# === Constants ===
DEVICE_FILE = Path("app/data/devices.json")  # Path to JSON file storing device data


# === Load & Save ===

def load_devices():
    """
    Load all devices from the JSON file.
    Returns a dictionary keyed by device_id.
    """
    if DEVICE_FILE.exists():
        with open(DEVICE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_devices(devices: dict):
    """
    Save the full devices dictionary back to the JSON file.
    """
    with open(DEVICE_FILE, "w") as f:
        json.dump(devices, f, indent=2)


# === Device CRUD ===

def get_device(device_id: str):
    """
    Return a single device by its ID, or None if not found.
    """
    return load_devices().get(device_id)

def register_or_update_device(device_id: str, name: str = None, active_playlist: str = None):
    """
    Register a new device or update an existing one.
    - Sets or updates `name` and `active_playlist`
    - Always updates `last_seen` timestamp
    - Automatically assigns `auth_token` if missing
    """
    devices = load_devices()
    now = datetime.utcnow().isoformat()

    if device_id not in devices:
        # --- Create new device record ---
        devices[device_id] = {
            "name": name or f"Unnamed Device ({device_id})",
            "active_playlist": active_playlist or "",
            "auth_token": str(uuid.uuid4()),  # ✅ Token issued on registration
            "last_seen": now,
            "active": False
        }
    else:
        # --- Update existing device ---
        if name:
            devices[device_id]["name"] = name
        if active_playlist is not None:
            devices[device_id]["active_playlist"] = active_playlist
        if "auth_token" not in devices[device_id]:  # ✅ Backfill token if missing
            devices[device_id]["auth_token"] = str(uuid.uuid4())
        devices[device_id]["last_seen"] = now

    save_devices(devices)


# === Playlist Assignment ===

def set_active_playlist(device_id: str, playlist_name: str):
    """
    Assign or update the active playlist for a given device.
    """
    devices = load_devices()
    if device_id in devices:
        devices[device_id]["active_playlist"] = playlist_name
        devices[device_id]["last_seen"] = datetime.utcnow().isoformat()
        save_devices(devices)
        return True
    return False


# === Token Management ===

def rotate_auth_token(device_id: str):
    """
    Replace the current auth_token with a new one for the device.
    Returns the new token, or None if the device is not found.
    """
    devices = load_devices()
    if device_id in devices:
        devices[device_id]["auth_token"] = str(uuid.uuid4())
        save_devices(devices)
        return devices[device_id]["auth_token"]
    return None


# === Playlist-to-Device Mapping ===

def get_assigned_devices_by_playlist(devices: dict):
    """
    Create a mapping of playlists → list of device names assigned to that playlist.
    Useful for rendering on the playlists UI.
    Example return:
      {
        "Cornerstone Sanctuary": ["Lobby TV", "Welcome Kiosk"],
        "Kids Wing": ["Check-in Station 1"]
      }
    """
    assigned = {}
    for device_id, device in devices.items():
        playlist = device.get("active_playlist")
        name = device.get("name", device_id)  # fallback to ID if name missing
        if playlist:
            assigned.setdefault(playlist, []).append(name)
    return assigned
