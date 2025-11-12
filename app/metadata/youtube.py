"""YouTube Data API integration for metadata enrichment."""
import requests
from typing import Dict, Optional
from app.config import settings

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"


def search_video(query: str, limit: int = 1) -> Optional[Dict]:
    """
    Search for videos on YouTube.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        Video dictionary or None
    """
    if not settings.YOUTUBE_API_KEY:
        return None
    
    try:
        params = {
            "part": "snippet,contentDetails",
            "q": query,
            "type": "video",
            "maxResults": limit,
            "key": settings.YOUTUBE_API_KEY
        }
        
        response = requests.get(
            f"{YOUTUBE_API_URL}/search",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            return None
        
        video = items[0]
        video_id = video["id"]["videoId"]
        
        # Get video details for duration
        details_params = {
            "part": "contentDetails",
            "id": video_id,
            "key": settings.YOUTUBE_API_KEY
        }
        
        details_response = requests.get(
            f"{YOUTUBE_API_URL}/videos",
            params=details_params,
            timeout=10
        )
        details_response.raise_for_status()
        
        details_data = details_response.json()
        video_details = details_data.get("items", [{}])[0]
        
        snippet = video["snippet"]
        
        # Parse duration (ISO 8601 format)
        duration_str = video_details.get("contentDetails", {}).get("duration", "")
        duration_seconds = _parse_duration(duration_str)
        
        return {
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "channel_title": snippet.get("channelTitle"),
            "published_at": snippet.get("publishedAt"),
            "youtube_id": video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            "duration": duration_seconds,
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url")
        }
    except Exception as e:
        print(f"YouTube search error: {e}")
        return None


def _parse_duration(duration_str: str) -> Optional[int]:
    """Parse ISO 8601 duration string to seconds."""
    if not duration_str:
        return None
    
    try:
        # Remove PT prefix
        duration_str = duration_str.replace("PT", "")
        seconds = 0
        
        if "H" in duration_str:
            hours, duration_str = duration_str.split("H")
            seconds += int(hours) * 3600
        
        if "M" in duration_str:
            minutes, duration_str = duration_str.split("M")
            seconds += int(minutes) * 60
        
        if "S" in duration_str:
            seconds_str = duration_str.replace("S", "")
            seconds += int(seconds_str)
        
        return seconds
    except Exception:
        return None


def enrich_metadata(title: str, artist: Optional[str] = None, game_name: Optional[str] = None) -> Optional[Dict]:
    """
    Enrich metadata using YouTube.
    
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
    query_parts.append("soundtrack")
    
    query = " ".join(query_parts)
    video = search_video(query, limit=1)
    
    if not video:
        return None
    
    metadata = {
        "title": video.get("title"),
        "description": video.get("description"),
        "youtube_id": video.get("youtube_id"),
        "youtube_url": video.get("youtube_url"),
        "duration": video.get("duration"),
    }
    
    # Try to extract artist from channel title
    if video.get("channel_title"):
        metadata["artists"] = [video["channel_title"]]
    
    return metadata

