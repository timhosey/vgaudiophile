"""Discogs API integration for metadata enrichment."""
import requests
from typing import Dict, Optional, List
from app.config import settings

DISCOGS_API_URL = "https://api.discogs.com"


def search_release(query: str, limit: int = 5) -> List[Dict]:
    """
    Search for releases on Discogs.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of release dictionaries
    """
    try:
        headers = {
            "User-Agent": settings.MUSICBRAINZ_USER_AGENT,  # Discogs requires User-Agent
        }
        
        if settings.DISCOGS_TOKEN:
            headers["Authorization"] = f"Discogs token={settings.DISCOGS_TOKEN}"
        
        params = {
            "q": query,
            "type": "release",
            "per_page": limit
        }
        
        response = requests.get(
            f"{DISCOGS_API_URL}/database/search",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"Discogs search error: {e}")
        return []


def get_release_by_id(release_id: int) -> Optional[Dict]:
    """
    Get release details by Discogs ID.
    
    Args:
        release_id: Discogs release ID
        
    Returns:
        Release dictionary or None
    """
    try:
        headers = {
            "User-Agent": settings.MUSICBRAINZ_USER_AGENT,
        }
        
        if settings.DISCOGS_TOKEN:
            headers["Authorization"] = f"Discogs token={settings.DISCOGS_TOKEN}"
        
        response = requests.get(
            f"{DISCOGS_API_URL}/releases/{release_id}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        print(f"Discogs get release error: {e}")
        return None


def enrich_metadata(title: str, artist: Optional[str] = None, game_name: Optional[str] = None) -> Optional[Dict]:
    """
    Enrich metadata using Discogs.
    
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
    
    if not query_parts:
        return None
    
    query = " ".join(query_parts)
    releases = search_release(query, limit=1)
    
    if not releases:
        return None
    
    release = releases[0]
    release_id = release.get("id")
    
    # Get full release details
    full_release = get_release_by_id(release_id)
    if not full_release:
        return None
    
    # Extract relevant metadata
    metadata = {
        "title": full_release.get("title"),
        "year": full_release.get("year"),
        "genre": ", ".join(full_release.get("genres", [])),
        "discogs_id": release_id,
        "discogs_url": full_release.get("uri"),
    }
    
    # Extract artists
    if "artists" in full_release:
        metadata["artists"] = [artist.get("name") for artist in full_release["artists"]]
    
    # Extract tracklist
    if "tracklist" in full_release:
        tracks = full_release["tracklist"]
        for i, track in enumerate(tracks, 1):
            if track.get("title", "").lower() == title.lower():
                metadata["track_number"] = i
                break
    
    return metadata

