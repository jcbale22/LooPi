"""
Service: Metadata Service
Purpose: Manages reading/writing of image metadata such as filename, 
         display date ranges, and associated playlists.
"""

import os
import json
from datetime import datetime
from typing import Dict, List

# === Path to metadata JSON file ===
METADATA_FILE = "metadata.json"

# === Ensure the metadata file exists at startup ===
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "w") as f:
        json.dump({}, f, indent=2)


def load_metadata() -> Dict:
    """
    Loads metadata dictionary from the file.
    Returns:
        dict: A dictionary where each key is a filename and the value contains its metadata.
    """
    with open(METADATA_FILE, "r") as f:
        return json.load(f)


def save_metadata(data: Dict) -> None:
    """
    Saves the provided metadata dictionary to the file.
    Args:
        data (dict): The metadata dictionary to persist.
    """
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def delete_file_metadata(filename: str) -> None:
    """
    Deletes metadata associated with a specific file.
    Args:
        filename (str): The name of the file to remove.
    """
    metadata = load_metadata()
    if filename in metadata:
        del metadata[filename]
        save_metadata(metadata)


def update_file_metadata(filename: str, start: str, end: str, playlists: List[str]) -> None:
    """
    Adds or updates a file's metadata entry.
    Args:
        filename (str): Name of the uploaded file.
        start (str): Start date in YYYY-MM-DD format.
        end (str): End date in YYYY-MM-DD format.
        playlists (list[str]): Playlists associated with the file.
    """
    metadata = load_metadata()
    metadata[filename] = {
        "start": start,
        "end": end,
        "playlists": playlists
    }
    save_metadata(metadata)


def get_active_images(today: datetime.date = None) -> List[str]:
    """
    Returns a list of image filenames that are active today.
    Args:
        today (date, optional): Defaults to today’s date. Used for testing/flexibility.
    Returns:
        list[str]: Active image filenames.
    """
    metadata = load_metadata()
    active = []
    today = today or datetime.today().date()

    for filename, info in metadata.items():
        try:
            start = datetime.strptime(info["start"], "%Y-%m-%d").date()
            end = datetime.strptime(info["end"], "%Y-%m-%d").date()
            if start <= today <= end:
                active.append(filename)
        except Exception as e:
            print(f"[WARN] Failed parsing date for {filename}: {e}")

    return acti
