"""Extract metadata from audio file tags using mutagen."""
from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError
from typing import Dict, Optional, List
import os


def extract_metadata(file_path: str) -> Dict[str, any]:
    """
    Extract metadata from an audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dictionary containing extracted metadata
    """
    metadata = {
        "title": None,
        "artist": None,
        "artists": [],
        "album": None,
        "game_name": None,
        "year": None,
        "genre": None,
        "track_number": None,
        "disc_number": None,
        "duration": None,
        "description": None,
    }
    
    try:
        audio_file = MutagenFile(file_path)
        if audio_file is None:
            return metadata
        
        # Get file size
        file_size = os.path.getsize(file_path)
        metadata["file_size"] = file_size
        
        # Get duration
        if hasattr(audio_file, "info") and hasattr(audio_file.info, "length"):
            metadata["duration"] = int(audio_file.info.length)
        
        # Extract tags based on file type
        if hasattr(audio_file, "tags"):
            tags = audio_file.tags
            
            # Common tag mappings
            tag_mappings = {
                "TIT2": "title",  # ID3v2.3/2.4
                "TITLE": "title",  # Vorbis, MP4
                "\xa9nam": "title",  # MP4
                "TIT1": "game_name",  # ID3v2 Content Group
                "TALB": "album",  # ID3v2 Album
                "ALBUM": "album",  # Vorbis, MP4
                "\xa9alb": "album",  # MP4
                "TPE1": "artist",  # ID3v2 Artist
                "ARTIST": "artist",  # Vorbis, MP4
                "\xa9ART": "artist",  # MP4
                "TDRC": "year",  # ID3v2 Date
                "DATE": "year",  # Vorbis
                "\xa9day": "year",  # MP4
                "TCON": "genre",  # ID3v2 Genre
                "GENRE": "genre",  # Vorbis, MP4
                "\xa9gen": "genre",  # MP4
                "TRCK": "track_number",  # ID3v2 Track
                "TRACKNUMBER": "track_number",  # Vorbis, MP4
                "trkn": "track_number",  # MP4
                "TPOS": "disc_number",  # ID3v2 Disc
                "DISCNUMBER": "disc_number",  # Vorbis, MP4
                "disk": "disc_number",  # MP4
                "COMM": "description",  # ID3v2 Comment
                "COMMENT": "description",  # Vorbis
                "\xa9cmt": "description",  # MP4
            }
            
            # Extract tags
            for tag_key, metadata_key in tag_mappings.items():
                if tag_key in tags:
                    value = tags[tag_key]
                    if isinstance(value, list) and len(value) > 0:
                        value = value[0]
                    if isinstance(value, str):
                        # Clean up the value
                        value = value.strip()
                        if value:
                            if metadata_key == "year":
                                # Extract year from date string
                                try:
                                    year_str = value.split("-")[0] if "-" in value else value.split("/")[0] if "/" in value else value
                                    metadata[metadata_key] = int(year_str[:4])
                                except (ValueError, IndexError):
                                    pass
                            elif metadata_key == "track_number":
                                # Extract track number (handle "1/10" format)
                                try:
                                    track_str = value.split("/")[0] if "/" in value else value
                                    metadata[metadata_key] = int(track_str)
                                except ValueError:
                                    pass
                            elif metadata_key == "disc_number":
                                # Extract disc number (handle "1/2" format)
                                try:
                                    disc_str = value.split("/")[0] if "/" in value else value
                                    metadata[metadata_key] = int(disc_str)
                                except ValueError:
                                    pass
                            else:
                                metadata[metadata_key] = value
            
            # Handle multiple artists
            artist_fields = ["TPE1", "ARTIST", "\xa9ART"]
            for field in artist_fields:
                if field in tags:
                    artists = tags[field]
                    if isinstance(artists, list):
                        metadata["artists"].extend([str(a).strip() for a in artists if str(a).strip()])
                    elif isinstance(artists, str):
                        # Split by common delimiters
                        for delimiter in [";", "/", ",", " & "]:
                            if delimiter in artists:
                                metadata["artists"].extend([a.strip() for a in artists.split(delimiter)])
                                break
                        else:
                            metadata["artists"].append(artists.strip())
            
            # If we have a single artist field but no artists list, use it
            if metadata["artist"] and not metadata["artists"]:
                metadata["artists"] = [metadata["artist"]]
            
            # Remove duplicates from artists list
            metadata["artists"] = list(dict.fromkeys(metadata["artists"]))
            
            # Try to extract game name from various fields
            if not metadata["game_name"]:
                # Check album for game name patterns
                if metadata["album"]:
                    # Common patterns: "Game Name OST", "Game Name Soundtrack"
                    album_lower = metadata["album"].lower()
                    for suffix in [" ost", " soundtrack", " - ost", " - soundtrack"]:
                        if album_lower.endswith(suffix):
                            metadata["game_name"] = metadata["album"][:-len(suffix)].strip()
                            break
            
    except ID3NoHeaderError:
        pass
    except Exception as e:
        # Don't print every error - let the scanner aggregate them
        # Just raise the exception so scanner can handle it
        raise
    
    return metadata

