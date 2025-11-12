"""SoundCloud API integration for metadata enrichment."""
import requests
from typing import Dict, Optional
from app.config import settings

SOUNDCLOUD_API_URL = "https://api.soundcloud.com"


def search_track(query: str, limit: int = 1) -> Optional[Dict]:
    """
    Search for tracks on SoundCloud.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        Track dictionary or None
    """
    if not settings.SOUNDCLOUD_CLIENT_ID:
        return None
    
    try:
        params = {
            "q": query,
            "limit": limit,
            "client_id": settings.SOUNDCLOUD_CLIENT_ID
        }
        
        response = requests.get(
            f"{SOUNDCLOUD_API_URL}/tracks",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if not data:
            return None
        
        track = data[0]
        
        return {
            "title": track.get("title"),
            "description": track.get("description"),
            "duration": track.get("duration") // 1000 if track.get("duration") else None,  # Convert ms to seconds
            "genre": track.get("genre"),
            "release_year": track.get("release_year"),
            "soundcloud_id": track.get("id"),
            "soundcloud_url": track.get("permalink_url"),
            "artwork_url": track.get("artwork_url"),
            "user": track.get("user", {}).get("username") if track.get("user") else None
        }
    except Exception as e:
        print(f"SoundCloud search error: {e}")
        return None


def enrich_metadata(title: str, artist: Optional[str] = None, game_name: Optional[str] = None) -> Optional[Dict]:
    """
    Enrich metadata using SoundCloud.
    
    Args:
        title: Track title
        artist: Artist name (optional)
        game_name: Game name (optional)
        
    Returns:
        Enriched metadata dictionary or None
    """
    # Build search query
    query_parts = []
    if title:
        query_parts.append(title)
    if artist:
        query_parts.append(artist)
    if game_name:
        query_parts.append(game_name)
    
    query = " ".join(query_parts)
    track = search_track(query, limit=1)
    
    if not track:
        return None
    
    metadata = {
        "title": track.get("title"),
        "description": track.get("description"),
        "duration": track.get("duration"),
        "genre": track.get("genre"),
        "year": track.get("release_year"),
        "soundcloud_id": track.get("soundcloud_id"),
        "soundcloud_url": track.get("soundcloud_url"),
    }
    
    # Extract artist from user field
    if track.get("user"):
        metadata["artists"] = [track["user"]]
    
    return metadata

