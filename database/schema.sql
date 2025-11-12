-- VGAudiophile Database Schema

CREATE DATABASE IF NOT EXISTS vgaudiophile CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE vgaudiophile;

-- Artists table
CREATE TABLE IF NOT EXISTS artists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Soundtracks table
CREATE TABLE IF NOT EXISTS soundtracks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    game_name VARCHAR(500),
    release_type ENUM('game_rip', 'remix_album', 'online_album', 'official_release', 'other') DEFAULT 'other',
    source_type ENUM('file', 'youtube', 'soundcloud', 'other') DEFAULT 'file',
    file_path VARCHAR(1000),
    file_size BIGINT,
    duration INT,
    track_number INT,
    disc_number INT,
    year INT,
    genre VARCHAR(255),
    album VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_game_name (game_name),
    INDEX idx_title (title),
    INDEX idx_release_type (release_type),
    INDEX idx_source_type (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Soundtrack-Artist relationship table
CREATE TABLE IF NOT EXISTS soundtrack_artists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    soundtrack_id INT NOT NULL,
    artist_id INT NOT NULL,
    role VARCHAR(100) DEFAULT 'artist',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (soundtrack_id) REFERENCES soundtracks(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
    UNIQUE KEY unique_soundtrack_artist (soundtrack_id, artist_id, role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Soundtrack-Tag relationship table
CREATE TABLE IF NOT EXISTS soundtrack_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    soundtrack_id INT NOT NULL,
    tag_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (soundtrack_id) REFERENCES soundtracks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE KEY unique_soundtrack_tag (soundtrack_id, tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Metadata sources table
CREATE TABLE IF NOT EXISTS metadata_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    soundtrack_id INT NOT NULL,
    source_type ENUM('musicbrainz', 'discogs', 'youtube', 'soundcloud', 'file_tags') NOT NULL,
    source_id VARCHAR(500),
    source_url VARCHAR(1000),
    metadata_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (soundtrack_id) REFERENCES soundtracks(id) ON DELETE CASCADE,
    INDEX idx_source_type (source_type),
    INDEX idx_source_id (source_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scan history table
CREATE TABLE IF NOT EXISTS scan_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    directory_path VARCHAR(1000) NOT NULL,
    files_scanned INT DEFAULT 0,
    files_added INT DEFAULT 0,
    files_updated INT DEFAULT 0,
    errors TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

