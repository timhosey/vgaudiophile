"""MusicBrainz API integration for metadata enrichment."""
import requests
from typing import Dict, Optional, List
from app.config import settings

MUSICBRAINZ_API_URL = "https://musicbrainz.org/ws/2"


def search_release(query: str, limit: int = 5) -> List[Dict]:
    """
    Search for releases on MusicBrainz.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of release dictionaries
    """
    try:
        headers = {
            "User-Agent": settings.MUSICBRAINZ_USER_AGENT,
            "Accept": "application/json"
        }
        
        params = {
            "query": query,
            "limit": limit,
            "fmt": "json"
        }
        
        response = requests.get(
            f"{MUSICBRAINZ_API_URL}/release",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("releases", [])
    except Exception as e:
        print(f"MusicBrainz search error: {e}")
        return []


def get_release_by_id(release_id: str) -> Optional[Dict]:
    """
    Get release details by MusicBrainz ID.
    
    Args:
        release_id: MusicBrainz release ID
        
    Returns:
        Release dictionary or None
    """
    try:
        headers = {
            "User-Agent": settings.MUSICBRAINZ_USER_AGENT,
            "Accept": "application/json"
        }
        
        response = requests.get(
            f"{MUSICBRAINZ_API_URL}/release/{release_id}",
            headers=headers,
            params={"inc": "artists+recordings"},
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        print(f"MusicBrainz get release error: {e}")
        return None


def enrich_metadata(title: str, artist: Optional[str] = None, game_name: Optional[str] = None) -> Optional[Dict]:
    """
    Enrich metadata using MusicBrainz.
    
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
        query_parts.append(f'title:"{title}"')
    if artist:
        query_parts.append(f'artist:"{artist}"')
    if game_name:
        query_parts.append(f'"{game_name}"')
    
    if not query_parts:
        return None
    
    query = " AND ".join(query_parts)
    releases = search_release(query, limit=1)
    
    if not releases:
        return None
    
    release = releases[0]
    
    # Extract relevant metadata
    metadata = {
        "title": release.get("title"),
        "year": release.get("date")[:4] if release.get("date") else None,
        "musicbrainz_id": release.get("id"),
        "musicbrainz_url": f"https://musicbrainz.org/release/{release.get('id')}",
    }
    
    # Get full release details
    full_release = get_release_by_id(release.get("id"))
    if full_release:
        # Extract artists
        if "artist-credit" in full_release:
            artists = []
            for credit in full_release["artist-credit"]:
                if "artist" in credit:
                    artists.append(credit["artist"].get("name"))
            metadata["artists"] = artists
        
        # Extract tracks
        if "media" in full_release and len(full_release["media"]) > 0:
            tracks = full_release["media"][0].get("tracks", [])
            for track in tracks:
                if track.get("title", "").lower() == title.lower():
                    metadata["track_number"] = track.get("position")
                    break
    
    return metadata

