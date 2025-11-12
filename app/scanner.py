"""Directory scanner for audio files."""
import os
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.database import (
    Soundtrack, Artist, SoundtrackArtist, Tag, SoundtrackTag,
    MetadataSource, ScanHistory, ScanStatus, ReleaseType, SourceType,
    MetadataSourceType
)
from app.metadata.file_tags import extract_metadata
from app.config import settings


def scan_directory(directory_path: str, db: Session, scan_history_id: Optional[int] = None) -> ScanHistory:
    """
    Scan a directory for audio files and add them to the database.
    
    Args:
        directory_path: Path to directory to scan
        db: Database session
        scan_history_id: Optional ID of existing scan_history to update
        
    Returns:
        ScanHistory object
    """
    # Get or create scan history entry
    if scan_history_id:
        scan_history = db.query(ScanHistory).filter(ScanHistory.id == scan_history_id).first()
        if not scan_history:
            raise ValueError(f"Scan history {scan_history_id} not found")
        # Update directory path if it changed
        if scan_history.directory_path != directory_path:
            scan_history.directory_path = directory_path
        # Ensure status is RUNNING
        if scan_history.status != ScanStatus.RUNNING:
            scan_history.status = ScanStatus.RUNNING
        db.commit()
        db.refresh(scan_history)
    else:
        # Create scan history entry
        scan_history = ScanHistory(
            directory_path=directory_path,
            status=ScanStatus.RUNNING
        )
        db.add(scan_history)
        db.commit()
        db.refresh(scan_history)
    
    files_scanned = 0
    files_added = 0
    files_updated = 0
    errors = []
    
    try:
        # Normalize directory path
        if not os.path.isabs(directory_path):
            # If relative, use MUSIC_DIRECTORY as base
            base_dir = settings.MUSIC_DIRECTORY
            directory_path = os.path.join(base_dir, directory_path)
        
        directory_path = os.path.normpath(directory_path)
        
        if not os.path.exists(directory_path):
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"Path is not a directory: {directory_path}")
        
        # Find all audio files
        audio_files = find_audio_files(directory_path)
        total_files = len(audio_files)
        
        # Update scan history with total files found
        scan_history.files_scanned = total_files
        db.commit()
        db.refresh(scan_history)
        
        # Process each file
        for idx, file_path in enumerate(audio_files, 1):
            try:
                added, updated = process_audio_file(file_path, directory_path, db)
                if added:
                    files_added += 1
                if updated:
                    files_updated += 1
                
                # Update scan history every 50 files or at the end
                # Keep files_scanned as total, don't overwrite it
                if idx % 50 == 0 or idx == total_files:
                    scan_history.files_added = files_added
                    scan_history.files_updated = files_updated
                    if errors:
                        scan_history.errors = "\n".join(errors[:10])  # Limit error text
                    db.commit()
                    db.refresh(scan_history)
                    
            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                errors.append(error_msg)
                print(error_msg)
        
        # Final update scan history
        scan_history.files_scanned = total_files
        scan_history.files_added = files_added
        scan_history.files_updated = files_updated
        scan_history.status = ScanStatus.COMPLETED
        if errors:
            # Store all errors, but limit display length
            error_text = "\n".join(errors)
            if len(error_text) > 10000:  # Limit to 10KB
                error_text = error_text[:10000] + f"\n... ({len(errors) - len(errors[:100])} more errors)"
            scan_history.errors = error_text
        
    except Exception as e:
        scan_history.status = ScanStatus.FAILED
        scan_history.errors = str(e)
        errors.append(str(e))
    
    finally:
        from datetime import datetime
        scan_history.completed_at = datetime.utcnow()
        db.commit()
    
    return scan_history


def find_audio_files(directory_path: str) -> List[str]:
    """
    Recursively find all audio files in a directory.
    
    Args:
        directory_path: Path to directory to scan
        
    Returns:
        List of audio file paths
    """
    audio_files = []
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # Skip hidden/system files (macOS resource forks, etc.)
            if file.startswith('._') or file.startswith('.'):
                continue
            
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            if file_ext in settings.SUPPORTED_FORMATS:
                audio_files.append(file_path)
    
    return sorted(audio_files)


def process_audio_file(file_path: str, base_directory: str, db: Session) -> Tuple[bool, bool]:
    """
    Process a single audio file and add/update it in the database.
    
    Args:
        file_path: Full path to audio file
        base_directory: Base directory path (for relative paths)
        db: Database session
        
    Returns:
        Tuple of (added, updated) booleans
    """
    # Check if file already exists in database
    existing = db.query(Soundtrack).filter(
        Soundtrack.file_path == file_path
    ).first()
    
    # Extract metadata from file
    file_metadata = extract_metadata(file_path)
    
    # Determine release type from path
    release_type = determine_release_type(file_path, base_directory)
    
    # Create or update soundtrack
    if existing:
        # Update existing entry
        update_soundtrack_from_metadata(existing, file_metadata, release_type)
        db.commit()
        return False, True
    else:
        # Create new entry
        soundtrack = create_soundtrack_from_metadata(file_path, file_metadata, release_type, db)
        db.add(soundtrack)
        db.commit()
        db.refresh(soundtrack)
        
        # Add file tags metadata source
        metadata_source = MetadataSource(
            soundtrack_id=soundtrack.id,
            source_type=MetadataSourceType.FILE_TAGS,
            metadata_json=file_metadata
        )
        db.add(metadata_source)
        db.commit()
        
        return True, False


def determine_release_type(file_path: str, base_directory: str) -> ReleaseType:
    """
    Determine release type from file path.
    
    Args:
        file_path: Full path to audio file
        base_directory: Base directory path
        
    Returns:
        ReleaseType enum value
    """
    # Get relative path
    try:
        rel_path = os.path.relpath(file_path, base_directory)
        path_lower = rel_path.lower()
    except ValueError:
        # If paths are on different drives, use absolute path
        path_lower = file_path.lower()
    
    # Check for keywords in path
    if any(keyword in path_lower for keyword in ["rip", "extracted", "game files"]):
        return ReleaseType.GAME_RIP
    elif any(keyword in path_lower for keyword in ["remix", "remaster", "cover"]):
        return ReleaseType.REMIX_ALBUM
    elif any(keyword in path_lower for keyword in ["youtube", "soundcloud", "online"]):
        return ReleaseType.ONLINE_ALBUM
    elif any(keyword in path_lower for keyword in ["ost", "soundtrack", "official"]):
        return ReleaseType.OFFICIAL_RELEASE
    else:
        return ReleaseType.OTHER


def create_soundtrack_from_metadata(
    file_path: str,
    metadata: dict,
    release_type: ReleaseType,
    db: Session
) -> Soundtrack:
    """
    Create a Soundtrack object from metadata.
    
    Args:
        file_path: Path to audio file
        metadata: Extracted metadata dictionary
        release_type: Release type
        db: Database session
        
    Returns:
        Soundtrack object
    """
    soundtrack = Soundtrack(
        title=metadata.get("title") or os.path.splitext(os.path.basename(file_path))[0],
        game_name=metadata.get("game_name"),
        release_type=release_type,
        source_type=SourceType.FILE,
        file_path=file_path,
        file_size=metadata.get("file_size"),
        duration=metadata.get("duration"),
        track_number=metadata.get("track_number"),
        disc_number=metadata.get("disc_number"),
        year=metadata.get("year"),
        genre=metadata.get("genre"),
        album=metadata.get("album"),
        description=metadata.get("description")
    )
    
    # Add artists
    artists_list = metadata.get("artists", [])
    if not artists_list and metadata.get("artist"):
        artists_list = [metadata["artist"]]
    
    for artist_name in artists_list:
        if artist_name:
            # Get or create artist
            artist = db.query(Artist).filter(Artist.name == artist_name).first()
            if not artist:
                artist = Artist(name=artist_name)
                db.add(artist)
                db.flush()
            
            # Create relationship
            soundtrack_artist = SoundtrackArtist(
                soundtrack=soundtrack,
                artist=artist,
                role="artist"
            )
            soundtrack.artists.append(soundtrack_artist)
    
    return soundtrack


def update_soundtrack_from_metadata(
    soundtrack: Soundtrack,
    metadata: dict,
    release_type: ReleaseType
):
    """
    Update a Soundtrack object with new metadata.
    
    Args:
        soundtrack: Soundtrack object to update
        metadata: Extracted metadata dictionary
        release_type: Release type
    """
    if metadata.get("title") and not soundtrack.title:
        soundtrack.title = metadata["title"]
    if metadata.get("game_name") and not soundtrack.game_name:
        soundtrack.game_name = metadata["game_name"]
    if metadata.get("album") and not soundtrack.album:
        soundtrack.album = metadata["album"]
    if metadata.get("year") and not soundtrack.year:
        soundtrack.year = metadata["year"]
    if metadata.get("genre") and not soundtrack.genre:
        soundtrack.genre = metadata["genre"]
    if metadata.get("duration") and not soundtrack.duration:
        soundtrack.duration = metadata["duration"]
    if metadata.get("track_number") and not soundtrack.track_number:
        soundtrack.track_number = metadata["track_number"]
    if metadata.get("disc_number") and not soundtrack.disc_number:
        soundtrack.disc_number = metadata["disc_number"]
    if metadata.get("description") and not soundtrack.description:
        soundtrack.description = metadata["description"]
    if metadata.get("file_size") and not soundtrack.file_size:
        soundtrack.file_size = metadata["file_size"]
    
    # Update release type if not set
    if soundtrack.release_type == ReleaseType.OTHER:
        soundtrack.release_type = release_type

