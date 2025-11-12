"""Configuration management for VGAudiophile."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database settings
    DB_HOST: str = "db"
    DB_PORT: int = 3306
    DB_NAME: str = "vgaudiophile"
    DB_USER: str = "vgaudiophile"
    DB_PASSWORD: str = "vgaudiophile"
    
    # Application settings
    APP_PORT: int = 8000
    MUSIC_DIRECTORY: str = "/music"
    
    # MusicBrainz settings
    MUSICBRAINZ_USER_AGENT: str = "VGAudiophile/1.0"
    
    # Discogs API
    DISCOGS_TOKEN: Optional[str] = None
    
    # YouTube API
    YOUTUBE_API_KEY: Optional[str] = None
    
    # SoundCloud API
    SOUNDCLOUD_CLIENT_ID: Optional[str] = None
    
    # Supported audio formats
    SUPPORTED_FORMATS: list[str] = [".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wav"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

