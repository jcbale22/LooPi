# app/schemas/models.py

from typing import List
from pydantic import BaseModel, Field


# === FileMetadata Schema ===
# Represents an uploaded file with its display dates and assigned playlists
class FileMetadata(BaseModel):
    filename: str                            # Image file name
    start: str = Field(..., example="2025-06-01")   # Start date (ISO format)
    end: str = Field(..., example="2025-06-30")     # End date (ISO format)
    playlists: List[str] = []                # Associated playlists


# === PlaylistEntry Schema ===
# Represents a playlist name and display color
class PlaylistEntry(BaseModel):
    name: str                                # Playlist name (e.g., "Lobby")
    color: str = Field("#e0e0e0", example="#e0e0e0")  # Hex color for pill UI
