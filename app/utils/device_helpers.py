import uuid
from datetime import datetime

# Create a new device structure with auth token
def create_device_entry(name: str, playlist: str = "") -> dict:
    return {
        "name": name,
        "active_playlist": playlist,
        "auth_token": str(uuid.uuid4()),
        "last_seen": None
    }

# Check device auth (case: MVP UUID token match)
def is_device_authorized(device_data: dict, provided_token: str) -> bool:
    return device_data.get("auth_token") == provided_token