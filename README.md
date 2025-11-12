# VGAudiophile

A powerful tool for indexing, cataloguing, and properly tagging video game soundtracks. Whether they be game rips, remix albums, online albums (like YouTube or SoundCloud), or officially released content, VGAudiophile helps you organize and manage your collection.

## Features

- **Directory Scanning**: Recursively scan directories to discover and index audio files
- **Metadata Extraction**: Extract metadata from audio file tags (MP3, FLAC, OGG, M4A, etc.)
- **Metadata Enrichment**: Enrich metadata from multiple sources:
  - File tags (ID3, Vorbis comments, MP4 tags)
  - MusicBrainz API
  - Discogs API
  - YouTube Data API
  - SoundCloud API
- **Web Interface**: Modern web UI for browsing, searching, and managing your catalog
- **REST API**: Full REST API for programmatic access
- **Docker Support**: Easy deployment with Docker Compose

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla JavaScript with modern CSS
- **Database**: MariaDB
- **Containerization**: Docker Compose

## Prerequisites

- Docker and Docker Compose
- (Optional) API keys for external services:
  - Discogs API token
  - YouTube Data API key
  - SoundCloud Client ID

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd vgaudiophile
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Set up your music directory**:
   - Create a directory for your music files
   - Update `MUSIC_DIRECTORY` in `.env` or `docker-compose.yml`

4. **Start the services**:
   ```bash
   docker-compose up -d
   ```

5. **Access the web interface**:
   - Open your browser to `http://localhost:8000`

6. **Scan your music directory**:
   - Go to the "Scan" tab
   - Enter the directory path (relative to `MUSIC_DIRECTORY`)
   - Click "Start Scan"

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database Configuration
DB_HOST=db
DB_PORT=3306
DB_NAME=vgaudiophile
DB_USER=vgaudiophile
DB_PASSWORD=vgaudiophile
DB_ROOT_PASSWORD=rootpassword

# Application Configuration
APP_PORT=8000
MUSIC_DIRECTORY=/music

# MusicBrainz Configuration
MUSICBRAINZ_USER_AGENT=VGAudiophile/1.0 (https://github.com/yourusername/vgaudiophile)

# Discogs API Configuration (Optional)
DISCOGS_TOKEN=your_discogs_token_here

# YouTube Data API Configuration (Optional)
YOUTUBE_API_KEY=your_youtube_api_key_here

# SoundCloud API Configuration (Optional)
SOUNDCLOUD_CLIENT_ID=your_soundcloud_client_id_here
```

### Music Directory Setup

The `MUSIC_DIRECTORY` environment variable specifies where your music files are located. You can:

1. **Use a local directory**: Set `MUSIC_DIRECTORY` to a local path and mount it in `docker-compose.yml`:
   ```yaml
   volumes:
     - /path/to/your/music:/music:ro
   ```

2. **Use a volume**: Create a Docker volume and mount it

### API Keys

#### Discogs API Token
1. Go to https://www.discogs.com/settings/developers
2. Create a new application
3. Copy your personal access token

#### YouTube Data API Key
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Copy the API key

#### SoundCloud Client ID
1. Go to https://developers.soundcloud.com/
2. Register your application
3. Copy the Client ID

## API Documentation

### Endpoints

#### Scan Directory
```http
POST /api/scan
Content-Type: application/json

{
  "directory": "/path/to/directory"
}
```

#### List Soundtracks
```http
GET /api/soundtracks?skip=0&limit=100&search=query&game_name=Game&release_type=official_release&source_type=file
```

Query Parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records (default: 100, max: 1000)
- `search`: Search in title, album, game_name, description
- `game_name`: Filter by game name
- `release_type`: Filter by release type (game_rip, remix_album, online_album, official_release, other)
- `source_type`: Filter by source type (file, youtube, soundcloud, other)

#### Get Soundtrack
```http
GET /api/soundtracks/{id}
```

#### Update Soundtrack
```http
PUT /api/soundtracks/{id}
Content-Type: application/json

{
  "title": "New Title",
  "game_name": "Game Name",
  "release_type": "official_release",
  "year": 2023,
  "genre": "Video Game Music",
  "artist_ids": [1, 2, 3]
}
```

#### Enrich Metadata
```http
POST /api/soundtracks/{id}/enrich
Content-Type: application/json

{
  "sources": ["musicbrainz", "discogs", "youtube", "soundcloud"]
}
```

If `sources` is omitted, all available sources will be used.

#### List Artists
```http
GET /api/artists?skip=0&limit=100&search=query
```

#### Get Statistics
```http
GET /api/stats
```

Returns:
```json
{
  "total_soundtracks": 1234,
  "total_artists": 567,
  "by_release_type": {
    "official_release": 800,
    "game_rip": 300,
    "remix_album": 100,
    "online_album": 34
  },
  "by_source_type": {
    "file": 1200,
    "youtube": 30,
    "soundcloud": 4
  },
  "total_duration": 123456,
  "total_size": 9876543210
}
```

#### Get Scan History
```http
GET /api/scan-history?skip=0&limit=50
```

## Supported Audio Formats

- MP3 (.mp3)
- FLAC (.flac)
- OGG (.ogg)
- M4A (.m4a)
- AAC (.aac)
- WAV (.wav)

## Database Schema

The application uses MariaDB with the following main tables:

- `soundtracks`: Main catalog entries
- `artists`: Artist information
- `soundtrack_artists`: Many-to-many relationship between soundtracks and artists
- `tags`: Custom tags
- `soundtrack_tags`: Many-to-many relationship between soundtracks and tags
- `metadata_sources`: Track metadata source references
- `scan_history`: Directory scan history

See `database/schema.sql` for the complete schema.

## Development

### Running Locally (without Docker)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up MariaDB**:
   - Install MariaDB locally
   - Create database: `CREATE DATABASE vgaudiophile;`
   - Run schema: `mysql vgaudiophile < database/schema.sql`

3. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Update database connection settings

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Project Structure

```
vgaudiophile/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models and connection
│   ├── scanner.py           # Directory scanning logic
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API route handlers
│   │   └── models.py        # Pydantic models
│   └── metadata/
│       ├── __init__.py
│       ├── file_tags.py     # Extract from audio files
│       ├── musicbrainz.py   # MusicBrainz integration
│       ├── discogs.py       # Discogs integration
│       ├── youtube.py       # YouTube integration
│       ├── soundcloud.py    # SoundCloud integration
│       └── enricher.py      # Metadata enrichment orchestrator
├── database/
│   └── schema.sql           # MariaDB schema
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Troubleshooting

### Database Connection Issues

- Ensure MariaDB container is running: `docker-compose ps`
- Check database credentials in `.env`
- Verify database is initialized: `docker-compose logs db`

### Scan Not Finding Files

- Verify `MUSIC_DIRECTORY` is correctly set
- Check volume mount in `docker-compose.yml`
- Ensure directory path is relative to `MUSIC_DIRECTORY` or absolute

### Metadata Enrichment Not Working

- Verify API keys are set in `.env`
- Check API rate limits (especially YouTube and SoundCloud)
- Review application logs: `docker-compose logs app`

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]
