"""
Service: Playlist Service
Purpose: Manages reading/writing of playlist data and default playlist handling.
         Playlists include a display name and an associated color.
"""

import json
from pathlib import Path
from typing import Dict

# Path to the playlists JSON file
PLAYLIST_FILE = Path("playlists.json")

# Ensure playlist file exists on app boot
if not PLAYLIST_FILE.exists():
    with open(PLAYLIST_FILE, "w") as f:
        json.dump({}, f, indent=2)


def load_playlists() -> Dict[str, str]:
    """
    Loads the playlist dictionary from file.

    Returns:
        dict: Mapping of playlist name -> color (hex code).
    """
    with open(PLAYLIST_FILE, "r") as f:
        return json.load(f)


def save_playlists(playlists: Dict[str, str]) -> None:
    """
    Saves the provided playlists dictionary to file.

    Args:
        playlists: Dictionary of playlist name -> color (hex).
    """
    with open(PLAYLIST_FILE, "w") as f:
        json.dump(playlists, f, indent=2)


def add_playlist(name: str, color: str) -> None:
    """
    Adds a new playlist to the store.

    Args:
        name: The playlist's display name.
        color: The color code (e.g. '#ffcc00').
    """
    playlists = load_playlists()
    playlists[name] = color
    save_playlists(playlists)


def update_playlist_color(name: str, new_color: str) -> None:
    """
    Updates the color of an existing playlist.

    Args:
        name: Playlist to update.
        new_color: Hex color value.
    """
    playlists = load_playlists()
    if name in playlists:
        playlists[name] = new_color
        save_playlists(playlists)


def delete_playlist(name: str) -> None:
    """
    Deletes a playlist if it exists.

    Args:
        name: The playlist name to delete.
    """
    playlists = load_playlists()
    if name in playlists:
        del playlists[name]
        save_playlists(playlists)


def backfill_playlists_from_metadata(metadata: Dict) -> None:
    """
    Ensures all playlists found in metadata exist in the playlist store.
    Any missing ones will be added with a default color.

    Args:
        metadata: Metadata dictionary to scan for playlist usage.
    """
    used_playlists = {
        playlist for meta in metadata.values()
        for playlist in meta.get("playlists", [])
    }

    playlists = load_playlists()
    updated = False

    for pl in used_playlists:
        if pl not in playlists:
            playlists[pl] = "#e0e0e0"  # Default light gray
            updated = True

    if updated:
        save_playlists(playlists)
