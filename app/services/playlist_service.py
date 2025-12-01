# app/services/playlist_service.py

"""
Service: Playlist Service
Purpose: Manages reading/writing of playlist data and default playlist handling.
         Playlists include a display name, color, and ordered list of image filenames.
"""

import json
from pathlib import Path
from typing import Dict, List

# Path to the playlists JSON file
PLAYLIST_FILE = Path("playlists.json")

# Ensure playlist file exists on app boot
if not PLAYLIST_FILE.exists():
    with open(PLAYLIST_FILE, "w") as f:
        json.dump({}, f, indent=2)

# --- Sync to app.state.playlists ---
def sync_playlists_to_state():
    try:
        from app.main import app
        app.state.playlists = load_playlists()
    except Exception:
        pass  # Fail silently in early load or import loops

# --- Load / Save ---
def load_playlists() -> Dict[str, Dict[str, object]]:
    with open(PLAYLIST_FILE, "r") as f:
        raw = json.load(f)
    # Upgrade legacy string format
    for name, val in raw.items():
        if isinstance(val, str):
            raw[name] = {"color": val, "images": [], "devices": []}
        else:
            val.setdefault("color", "#e0e0e0")
            val.setdefault("images", [])
            val.setdefault("devices", [])
    return raw

def save_playlists(playlists: Dict[str, Dict[str, object]]) -> None:
    with open(PLAYLIST_FILE, "w") as f:
        json.dump(playlists, f, indent=2)
    sync_playlists_to_state()

# --- CRUD ---
def add_playlist(name: str, color: str) -> None:
    playlists = load_playlists()
    if name not in playlists:
        playlists[name] = {"color": color, "images": [], "devices": []}
        save_playlists(playlists)

def update_playlist_color(name: str, new_color: str) -> None:
    playlists = load_playlists()
    if name in playlists:
        playlists[name]["color"] = new_color
        save_playlists(playlists)

def delete_playlist(name: str) -> None:
    playlists = load_playlists()
    if name in playlists:
        del playlists[name]
        save_playlists(playlists)

# --- Image Operations ---
def get_playlist_images(name: str) -> List[str]:
    playlists = load_playlists()
    return playlists.get(name, {}).get("images", [])

def set_playlist_images(name: str, images: List[str]) -> None:
    playlists = load_playlists()
    if name in playlists:
        playlists[name]["images"] = images
        save_playlists(playlists)

def add_image_to_playlist(name: str, filename: str) -> None:
    playlists = load_playlists()
    if name in playlists:
        if filename not in playlists[name]["images"]:
            playlists[name]["images"].append(filename)
            save_playlists(playlists)

def remove_image_from_playlist(name: str, filename: str) -> None:
    playlists = load_playlists()
    if name in playlists and filename in playlists[name]["images"]:
        playlists[name]["images"].remove(filename)
        save_playlists(playlists)

def reorder_images_in_playlist(name: str, new_order: List[str]) -> None:
    playlists = load_playlists()
    if name in playlists:
        playlists[name]["images"] = new_order
        save_playlists(playlists)

# --- Metadata Backfill ---
def backfill_playlists_from_metadata(metadata: Dict) -> None:
    used_playlists = {
        playlist for meta in metadata.values()
        for playlist in meta.get("playlists", [])
    }

    playlists = load_playlists()
    updated = False

    for pl in used_playlists:
        if pl not in playlists:
            playlists[pl] = {
                "color": "#e0e0e0",
                "images": [],
                "devices": []
            }
            updated = True

    if updated:
        save_playlists(playlists)

# --- Device Assignment Utility ---
def get_assigned_devices_by_playlist(devices: Dict[str, Dict]) -> Dict[str, List[str]]:
    result = {}
    for info in devices.values():
        pl = info.get("active_playlist")
        name = info.get("name")
        if pl and name:
            result.setdefault(pl, []).append(name)
    return result


# --- Device Update Support ---
def update_playlist_device_assignments(devices: Dict[str, Dict]) -> None:
    playlists = load_playlists()
    # Clear current device mappings
    for p in playlists.values():
        p["devices"] = []

    # Rebuild device assignments using device *name*
    for device_info in devices.values():
        pl = device_info.get("active_playlist")
        name = device_info.get("name")
        if pl and name and pl in playlists:
            playlists[pl]["devices"].append(name)
    save_playlists(playlists)

