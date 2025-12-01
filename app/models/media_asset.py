from sqlmodel import SQLModel, Field
from typing import Optional

class MediaAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int  # Replace with dynamic user ID when available
    filename: str
    r2_key: str
    content_type: str
    size: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    playlists: Optional[str] = None  # Comma-separated string for simplicity
