"""API route handlers."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
import os
from app.database import (
    get_db, Soundtrack, Artist, SoundtrackArtist, ScanHistory,
    MetadataSource, MetadataSourceType, Tag, SoundtrackTag
)
from app.api.models import (
    SoundtrackResponse, SoundtrackUpdate, ScanRequest, ScanResponse,
    StatsResponse, EnrichRequest
)
from app.scanner import scan_directory
from app.metadata.enricher import enrich_from_all_sources
from app.metadata import musicbrainz, discogs, youtube, soundcloud
import json
import threading

router = APIRouter()


@router.post("/scan", response_model=ScanResponse)
def scan_directory_endpoint(
    request: ScanRequest, 
    db: Session = Depends(get_db)
):
    """Start scanning a directory for audio files (runs in background)."""
    try:
        # Create scan history entry immediately
        from app.database import ScanStatus
        scan_history = ScanHistory(
            directory_path=request.directory,
            status=ScanStatus.RUNNING
        )
        db.add(scan_history)
        db.commit()
        db.refresh(scan_history)
        
        # Run scan in background
        def run_scan():
            # Create a new database session for the background task
            from app.database import SessionLocal
            bg_db = SessionLocal()
            try:
                # Call scan_directory with the scan_history ID so it updates the existing entry
                scan_directory(request.directory, bg_db, scan_history_id=scan_history.id)
            except Exception as e:
                # Update scan history with error
                try:
                    scan_history_to_update = bg_db.query(ScanHistory).filter(
                        ScanHistory.id == scan_history.id
                    ).first()
                    if scan_history_to_update:
                        scan_history_to_update.status = ScanStatus.FAILED
                        scan_history_to_update.errors = str(e)
                        bg_db.commit()
                    print(f"Error in background scan: {e}")
                except Exception as db_error:
                    print(f"Error updating scan history: {db_error}")
            finally:
                bg_db.close()
        
        thread = threading.Thread(target=run_scan)
        thread.daemon = True
        thread.start()
        
        return scan_history
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/scan/{scan_id}", response_model=ScanResponse)
def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    """Get the current status of a scan."""
    scan_history = db.query(ScanHistory).filter(ScanHistory.id == scan_id).first()
    if not scan_history:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan_history


@router.get("/soundtracks", response_model=dict)
def list_soundtracks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    game_name: Optional[str] = Query(None),
    release_type: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    group_by: Optional[str] = Query(None, description="Group by: album, folder, or none"),
    db: Session = Depends(get_db)
):
    """List soundtracks with optional filtering and grouping."""
    query = db.query(Soundtrack)
    
    # Apply filters
    if search:
        search_filter = or_(
            Soundtrack.title.ilike(f"%{search}%"),
            Soundtrack.album.ilike(f"%{search}%"),
            Soundtrack.game_name.ilike(f"%{search}%"),
            Soundtrack.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if game_name:
        query = query.filter(Soundtrack.game_name.ilike(f"%{game_name}%"))
    
    if release_type:
        query = query.filter(Soundtrack.release_type == release_type)
    
    if source_type:
        query = query.filter(Soundtrack.source_type == source_type)
    
    # Get total count before pagination
    total = query.count()
    
    # Calculate pagination info
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    current_page = (skip // limit) + 1
    
    # Apply pagination and ordering
    soundtracks = query.order_by(Soundtrack.title).offset(skip).limit(limit).all()
    
    # Load artists for each soundtrack
    for soundtrack in soundtracks:
        soundtrack.artists = [
            sa.artist for sa in soundtrack.artists
        ]
    
    # Group soundtracks if requested
    grouped_data = None
    if group_by == "album":
        grouped = {}
        for st in soundtracks:
            album_key = st.album or "Unknown Album"
            if album_key not in grouped:
                grouped[album_key] = []
            grouped[album_key].append(st)
        grouped_data = grouped
    elif group_by == "folder":
        grouped = {}
        for st in soundtracks:
            if st.file_path:
                # Extract folder name from path
                folder = os.path.dirname(st.file_path).split(os.sep)[-1] or "Unknown Folder"
            else:
                folder = "Unknown Folder"
            if folder not in grouped:
                grouped[folder] = []
            grouped[folder].append(st)
        grouped_data = grouped
    
    result = {
        "soundtracks": soundtracks,
        "pagination": {
            "total": total,
            "page": current_page,
            "page_size": limit,
            "total_pages": total_pages,
            "has_next": skip + limit < total,
            "has_prev": skip > 0
        }
    }
    
    if grouped_data:
        result["grouped"] = grouped_data
    
    return result


@router.get("/soundtracks/{soundtrack_id}", response_model=SoundtrackResponse)
def get_soundtrack(soundtrack_id: int, db: Session = Depends(get_db)):
    """Get a specific soundtrack by ID."""
    soundtrack = db.query(Soundtrack).filter(Soundtrack.id == soundtrack_id).first()
    if not soundtrack:
        raise HTTPException(status_code=404, detail="Soundtrack not found")
    
    # Load artists
    soundtrack.artists = [sa.artist for sa in soundtrack.artists]
    
    return soundtrack


@router.put("/soundtracks/{soundtrack_id}", response_model=SoundtrackResponse)
def update_soundtrack(
    soundtrack_id: int,
    update: SoundtrackUpdate,
    db: Session = Depends(get_db)
):
    """Update a soundtrack's metadata."""
    soundtrack = db.query(Soundtrack).filter(Soundtrack.id == soundtrack_id).first()
    if not soundtrack:
        raise HTTPException(status_code=404, detail="Soundtrack not found")
    
    # Update fields
    update_data = update.dict(exclude_unset=True, exclude={"artist_ids"})
    for field, value in update_data.items():
        setattr(soundtrack, field, value)
    
    # Update artists if provided
    if update.artist_ids is not None:
        # Remove existing artist relationships
        db.query(SoundtrackArtist).filter(
            SoundtrackArtist.soundtrack_id == soundtrack_id
        ).delete()
        
        # Add new artist relationships
        for artist_id in update.artist_ids:
            artist = db.query(Artist).filter(Artist.id == artist_id).first()
            if artist:
                soundtrack_artist = SoundtrackArtist(
                    soundtrack_id=soundtrack_id,
                    artist_id=artist_id,
                    role="artist"
                )
                db.add(soundtrack_artist)
    
    db.commit()
    db.refresh(soundtrack)
    
    # Load artists
    soundtrack.artists = [sa.artist for sa in soundtrack.artists]
    
    return soundtrack


@router.post("/soundtracks/{soundtrack_id}/enrich", response_model=SoundtrackResponse)
def enrich_soundtrack_metadata(
    soundtrack_id: int,
    request: EnrichRequest,
    db: Session = Depends(get_db)
):
    """Enrich soundtrack metadata from external sources."""
    soundtrack = db.query(Soundtrack).filter(Soundtrack.id == soundtrack_id).first()
    if not soundtrack:
        raise HTTPException(status_code=404, detail="Soundtrack not found")
    
    # Determine which sources to use
    sources_to_use = request.sources if request.sources else [
        "musicbrainz", "discogs", "youtube", "soundcloud"
    ]
    
    # Enrich metadata
    enriched = enrich_from_all_sources(
        file_path=soundtrack.file_path,
        title=soundtrack.title,
        artist=soundtrack.artists[0].artist.name if soundtrack.artists else None,
        game_name=soundtrack.game_name
    )
    
    # Store metadata sources
    for source_name, source_data in enriched["sources"].items():
        if source_name not in sources_to_use:
            continue
        
        # Map source name to MetadataSourceType
        source_type_map = {
            "musicbrainz": MetadataSourceType.MUSICBRAINZ,
            "discogs": MetadataSourceType.DISCOGS,
            "youtube": MetadataSourceType.YOUTUBE,
            "soundcloud": MetadataSourceType.SOUNDCLOUD,
            "file_tags": MetadataSourceType.FILE_TAGS
        }
        
        source_type = source_type_map.get(source_name)
        if not source_type:
            continue
        
        # Check if metadata source already exists
        existing_source = db.query(MetadataSource).filter(
            MetadataSource.soundtrack_id == soundtrack_id,
            MetadataSource.source_type == source_type
        ).first()
        
        # Extract source ID and URL
        source_id = None
        source_url = None
        
        if source_name == "musicbrainz" and source_data.get("musicbrainz_id"):
            source_id = source_data["musicbrainz_id"]
            source_url = source_data.get("musicbrainz_url")
        elif source_name == "discogs" and source_data.get("discogs_id"):
            source_id = str(source_data["discogs_id"])
            source_url = source_data.get("discogs_url")
        elif source_name == "youtube" and source_data.get("youtube_id"):
            source_id = source_data["youtube_id"]
            source_url = source_data.get("youtube_url")
        elif source_name == "soundcloud" and source_data.get("soundcloud_id"):
            source_id = str(source_data["soundcloud_id"])
            source_url = source_data.get("soundcloud_url")
        
        if existing_source:
            # Update existing source
            existing_source.source_id = source_id
            existing_source.source_url = source_url
            existing_source.metadata_json = source_data
        else:
            # Create new source
            metadata_source = MetadataSource(
                soundtrack_id=soundtrack_id,
                source_type=source_type,
                source_id=source_id,
                source_url=source_url,
                metadata_json=source_data
            )
            db.add(metadata_source)
    
    # Update soundtrack with merged metadata (but don't overwrite existing values)
    merged = enriched["merged"]
    if merged.get("title") and not soundtrack.title:
        soundtrack.title = merged["title"]
    if merged.get("game_name") and not soundtrack.game_name:
        soundtrack.game_name = merged["game_name"]
    if merged.get("album") and not soundtrack.album:
        soundtrack.album = merged["album"]
    if merged.get("year") and not soundtrack.year:
        soundtrack.year = merged["year"]
    if merged.get("genre") and not soundtrack.genre:
        soundtrack.genre = merged["genre"]
    if merged.get("duration") and not soundtrack.duration:
        soundtrack.duration = merged["duration"]
    if merged.get("track_number") and not soundtrack.track_number:
        soundtrack.track_number = merged["track_number"]
    if merged.get("disc_number") and not soundtrack.disc_number:
        soundtrack.disc_number = merged["disc_number"]
    if merged.get("description") and not soundtrack.description:
        soundtrack.description = merged["description"]
    
    # Add new artists if any
    if merged.get("artists"):
        existing_artist_names = {sa.artist.name for sa in soundtrack.artists}
        for artist_name in merged["artists"]:
            if artist_name not in existing_artist_names:
                # Get or create artist
                artist = db.query(Artist).filter(Artist.name == artist_name).first()
                if not artist:
                    artist = Artist(name=artist_name)
                    db.add(artist)
                    db.flush()
                
                # Create relationship
                soundtrack_artist = SoundtrackArtist(
                    soundtrack_id=soundtrack_id,
                    artist_id=artist.id,
                    role="artist"
                )
                db.add(soundtrack_artist)
    
    db.commit()
    db.refresh(soundtrack)
    
    # Load artists
    soundtrack.artists = [sa.artist for sa in soundtrack.artists]
    
    return soundtrack


@router.get("/artists", response_model=List[dict])
def list_artists(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List artists."""
    query = db.query(Artist)
    
    if search:
        query = query.filter(Artist.name.ilike(f"%{search}%"))
    
    artists = query.order_by(Artist.name).offset(skip).limit(limit).all()
    
    return [{"id": a.id, "name": a.name} for a in artists]


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Get catalog statistics."""
    total_soundtracks = db.query(Soundtrack).count()
    total_artists = db.query(Artist).count()
    
    # Count by release type
    release_type_counts = db.query(
        Soundtrack.release_type,
        func.count(Soundtrack.id)
    ).group_by(Soundtrack.release_type).all()
    by_release_type = {str(rt): count for rt, count in release_type_counts}
    
    # Count by source type
    source_type_counts = db.query(
        Soundtrack.source_type,
        func.count(Soundtrack.id)
    ).group_by(Soundtrack.source_type).all()
    by_source_type = {str(st): count for st, count in source_type_counts}
    
    # Calculate total duration and size
    duration_sum = db.query(func.sum(Soundtrack.duration)).scalar()
    size_sum = db.query(func.sum(Soundtrack.file_size)).scalar()
    
    return StatsResponse(
        total_soundtracks=total_soundtracks,
        total_artists=total_artists,
        by_release_type=by_release_type,
        by_source_type=by_source_type,
        total_duration=int(duration_sum) if duration_sum else None,
        total_size=int(size_sum) if size_sum else None
    )


@router.get("/scan-history", response_model=List[ScanResponse])
def get_scan_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get scan history."""
    scans = db.query(ScanHistory).order_by(
        ScanHistory.started_at.desc()
    ).offset(skip).limit(limit).all()
    
    return scans


@router.delete("/admin/clear-all")
def clear_all_data(db: Session = Depends(get_db)):
    """
    Admin endpoint to clear all scanned data from the database.
    WARNING: This will delete all soundtracks, artists, tags, metadata sources, and scan history.
    """
    try:
        # Delete in order to respect foreign key constraints
        # Metadata sources (references soundtracks)
        db.query(MetadataSource).delete()
        
        # Soundtrack tags (references soundtracks and tags)
        db.query(SoundtrackTag).delete()
        
        # Soundtrack artists (references soundtracks and artists)
        db.query(SoundtrackArtist).delete()
        
        # Soundtracks
        db.query(Soundtrack).delete()
        
        # Scan history
        db.query(ScanHistory).delete()
        
        # Artists (no longer referenced)
        db.query(Artist).delete()
        
        # Tags (no longer referenced)
        db.query(Tag).delete()
        
        db.commit()
        
        return {
            "message": "All data cleared successfully",
            "deleted": {
                "soundtracks": "all",
                "artists": "all",
                "tags": "all",
                "metadata_sources": "all",
                "scan_history": "all"
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing data: {str(e)}")

