"""Metadata enrichment orchestrator."""
from typing import Dict, Optional, List
from app.metadata import file_tags, musicbrainz, discogs, youtube, soundcloud
from app.database import MetadataSourceType


def enrich_from_all_sources(
    file_path: Optional[str] = None,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    game_name: Optional[str] = None
) -> Dict[str, any]:
    """
    Enrich metadata from all available sources.
    
    Args:
        file_path: Path to audio file (for file tag extraction)
        title: Track title
        artist: Artist name
        game_name: Game name
        
    Returns:
        Dictionary containing enriched metadata from all sources
    """
    enriched = {
        "sources": {},
        "merged": {}
    }
    
    # Extract from file tags if file path provided
    if file_path:
        file_metadata = file_tags.extract_metadata(file_path)
        enriched["sources"]["file_tags"] = file_metadata
        # Use file metadata as base
        if not title and file_metadata.get("title"):
            title = file_metadata["title"]
        if not artist and file_metadata.get("artists"):
            artist = file_metadata["artists"][0]
        if not game_name and file_metadata.get("game_name"):
            game_name = file_metadata["game_name"]
    
    # Enrich from external sources
    if title:
        # MusicBrainz
        try:
            mb_metadata = musicbrainz.enrich_metadata(title, artist, game_name)
            if mb_metadata:
                enriched["sources"]["musicbrainz"] = mb_metadata
        except Exception as e:
            print(f"MusicBrainz enrichment error: {e}")
        
        # Discogs
        try:
            discogs_metadata = discogs.enrich_metadata(title, artist, game_name)
            if discogs_metadata:
                enriched["sources"]["discogs"] = discogs_metadata
        except Exception as e:
            print(f"Discogs enrichment error: {e}")
        
        # YouTube
        try:
            yt_metadata = youtube.enrich_metadata(title, artist, game_name)
            if yt_metadata:
                enriched["sources"]["youtube"] = yt_metadata
        except Exception as e:
            print(f"YouTube enrichment error: {e}")
        
        # SoundCloud
        try:
            sc_metadata = soundcloud.enrich_metadata(title, artist, game_name)
            if sc_metadata:
                enriched["sources"]["soundcloud"] = sc_metadata
        except Exception as e:
            print(f"SoundCloud enrichment error: {e}")
    
    # Merge metadata from all sources (file tags take precedence)
    enriched["merged"] = merge_metadata(enriched["sources"])
    
    return enriched


def merge_metadata(sources: Dict[str, Dict]) -> Dict[str, any]:
    """
    Merge metadata from multiple sources with conflict resolution.
    
    Priority order:
    1. file_tags (highest priority)
    2. musicbrainz
    3. discogs
    4. youtube
    5. soundcloud (lowest priority)
    
    Args:
        sources: Dictionary of source metadata
        
    Returns:
        Merged metadata dictionary
    """
    merged = {}
    priority_order = ["file_tags", "musicbrainz", "discogs", "youtube", "soundcloud"]
    
    # Merge fields in priority order
    for source_name in priority_order:
        if source_name in sources:
            source_data = sources[source_name]
            for key, value in source_data.items():
                if value is not None and key not in merged:
                    merged[key] = value
    
    # Special handling for artists list
    artists_set = set()
    for source_name in priority_order:
        if source_name in sources:
            source_artists = sources[source_name].get("artists", [])
            if isinstance(source_artists, list):
                artists_set.update(source_artists)
            elif source_artists:
                artists_set.add(source_artists)
    
    if artists_set:
        merged["artists"] = list(artists_set)
    
    return merged

