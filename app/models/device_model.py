# app/models/device_model.py

from typing import Dict

# A simple dict-based structure (replace with DB model if needed later)
class Device:
    def __init__(self, device_id: str, name: str = "", active_playlist: str = "", auth_token: str = "", active: bool = False):
        self.device_id = device_id
        self.name = name
        self.active_playlist = active_playlist
        self.auth_token = auth_token
        self.active = active

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "active_playlist": self.active_playlist,
            "auth_token": self.auth_token,
            "active": self.active
        }

    @staticmethod
    def from_dict(device_id: str, data: Dict):
        return Device(
            device_id=device_id,
            name=data.get("name", ""),
            active_playlist=data.get("active_playlist", ""),
            auth_token=data.get("auth_token", ""),
            active=data.get("active", False),
        )
