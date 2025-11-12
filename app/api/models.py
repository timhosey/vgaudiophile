"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.database import ReleaseType, SourceType


class ArtistResponse(BaseModel):
    """Artist response model."""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class SoundtrackResponse(BaseModel):
    """Soundtrack response model."""
    id: int
    title: str
    game_name: Optional[str] = None
    release_type: str
    source_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[int] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    album: Optional[str] = None
    description: Optional[str] = None
    artists: List[ArtistResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SoundtrackUpdate(BaseModel):
    """Soundtrack update model."""
    title: Optional[str] = None
    game_name: Optional[str] = None
    release_type: Optional[ReleaseType] = None
    source_type: Optional[SourceType] = None
    track_number: Optional[int] = None
    disc_number: Optional[int] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    album: Optional[str] = None
    description: Optional[str] = None
    artist_ids: Optional[List[int]] = None


class ScanRequest(BaseModel):
    """Scan request model."""
    directory: str = Field(..., description="Directory path to scan")


class ScanResponse(BaseModel):
    """Scan response model."""
    id: int
    directory_path: str
    files_scanned: int
    files_added: int
    files_updated: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    errors: Optional[str] = None
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Statistics response model."""
    total_soundtracks: int
    total_artists: int
    by_release_type: dict[str, int]
    by_source_type: dict[str, int]
    total_duration: Optional[int] = None  # Total duration in seconds
    total_size: Optional[int] = None  # Total file size in bytes


class EnrichRequest(BaseModel):
    """Metadata enrichment request model."""
    sources: Optional[List[str]] = Field(
        default=None,
        description="List of sources to use (musicbrainz, discogs, youtube, soundcloud). If None, uses all available."
    )

