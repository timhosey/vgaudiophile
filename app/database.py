"""Database connection and models."""
from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, BigInteger, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.config import settings

Base = declarative_base()


class ReleaseType(str, enum.Enum):
    """Release type enumeration."""
    GAME_RIP = "game_rip"
    REMIX_ALBUM = "remix_album"
    ONLINE_ALBUM = "online_album"
    OFFICIAL_RELEASE = "official_release"
    OTHER = "other"


class SourceType(str, enum.Enum):
    """Source type enumeration."""
    FILE = "file"
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    OTHER = "other"


class MetadataSourceType(str, enum.Enum):
    """Metadata source type enumeration."""
    MUSICBRAINZ = "musicbrainz"
    DISCOGS = "discogs"
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    FILE_TAGS = "file_tags"


class ScanStatus(str, enum.Enum):
    """Scan status enumeration."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Artist(Base):
    """Artist model."""
    __tablename__ = "artists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    soundtracks = relationship("SoundtrackArtist", back_populates="artist")


class Soundtrack(Base):
    """Soundtrack model."""
    __tablename__ = "soundtracks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    game_name = Column(String(500), index=True)
    release_type = Column(Enum(ReleaseType), default=ReleaseType.OTHER, index=True)
    source_type = Column(Enum(SourceType), default=SourceType.FILE, index=True)
    file_path = Column(String(1000))
    file_size = Column(BigInteger)
    duration = Column(Integer)  # Duration in seconds
    track_number = Column(Integer)
    disc_number = Column(Integer)
    year = Column(Integer)
    genre = Column(String(255))
    album = Column(String(500))
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    artists = relationship("SoundtrackArtist", back_populates="soundtrack", cascade="all, delete-orphan")
    tags = relationship("SoundtrackTag", back_populates="soundtrack", cascade="all, delete-orphan")
    metadata_sources = relationship("MetadataSource", back_populates="soundtrack", cascade="all, delete-orphan")


class SoundtrackArtist(Base):
    """Soundtrack-Artist relationship model."""
    __tablename__ = "soundtrack_artists"
    
    id = Column(Integer, primary_key=True, index=True)
    soundtrack_id = Column(Integer, ForeignKey("soundtracks.id", ondelete="CASCADE"), nullable=False)
    artist_id = Column(Integer, ForeignKey("artists.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(100), default="artist")
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    soundtrack = relationship("Soundtrack", back_populates="artists")
    artist = relationship("Artist", back_populates="soundtracks")


class Tag(Base):
    """Tag model."""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    soundtracks = relationship("SoundtrackTag", back_populates="tag")


class SoundtrackTag(Base):
    """Soundtrack-Tag relationship model."""
    __tablename__ = "soundtrack_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    soundtrack_id = Column(Integer, ForeignKey("soundtracks.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    soundtrack = relationship("Soundtrack", back_populates="tags")
    tag = relationship("Tag", back_populates="soundtracks")


class MetadataSource(Base):
    """Metadata source model."""
    __tablename__ = "metadata_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    soundtrack_id = Column(Integer, ForeignKey("soundtracks.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(Enum(MetadataSourceType), nullable=False, index=True)
    source_id = Column(String(500), index=True)
    source_url = Column(String(1000))
    metadata_json = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    soundtrack = relationship("Soundtrack", back_populates="metadata_sources")


class ScanHistory(Base):
    """Scan history model."""
    __tablename__ = "scan_history"
    
    id = Column(Integer, primary_key=True, index=True)
    directory_path = Column(String(1000), nullable=False)
    files_scanned = Column(Integer, default=0)
    files_added = Column(Integer, default=0)
    files_updated = Column(Integer, default=0)
    errors = Column(Text)
    started_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    completed_at = Column(TIMESTAMP)
    status = Column(Enum(ScanStatus), default=ScanStatus.RUNNING, index=True)


# Database connection
DATABASE_URL = f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

