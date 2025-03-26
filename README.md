# SentenceTransformer-search Project

## Overview
A comprehensive system for collecting, processing, and searching text games (CYOA) with semantic capabilities.

## Key Features
- Automated game downloading and processing
- AI-powered summarization and cataloging
- Visual analysis of game screenshots
- Semantic search capabilities
- Comprehensive logging and error handling

## Main Components

### Core Scripts
- **controller.py** - Main orchestrator that manages:
  - Game downloading (via project_downloader.py)
  - Content extraction (via crawler/js_json_extractor/traffic_analyzer)
  - Screenshot generation (get_screenshoot_puppy.js)
  - Summary generation (summarize.py)
  - Catalog updates (prepare_and_upload.py)

- **summarize.py** - Generates structured descriptions:
  - Two modes: `sent_search` (searchable summaries) and `catalog` (JSON entries)
  - Integrates visual analysis from screenshots
  - Uses CSV metadata for enhanced descriptions

- **project_downloader.py** - Handles game downloads:
  - Concurrent downloads with ETag-based caching
  - Resource discovery and metadata tracking
  - Session management for efficient downloads

### Supporting Components
- **game_checker.py** - Manages game catalog
- **traffic_analyzer.py** - Network traffic analysis
- **js_json_extractor.py** - Extracts JSON from JavaScript
- **crawler.py** - Basic web crawler
- **vision_query.py** - Image analysis

## Usage

### Basic Processing

1. Add the link in links.txt - it's better to add one game at a time

2. Type
```bash 
python controller.py
```
3. Check the tags manually on the Moderator Panel


### Screenshot Replacement

```bash
python image_replacer.py "Cyoa title from catalog"
```
 

## File Structure
```
.
├── controller.py               # Main controller
├── components/
│   ├── game_checker.py         # Catalog management
│   ├── project_downloader.py   # Game downloader
│   ├── traffic_analyzer.py     # Network analysis
│   ├── js_json_extractor.py    # JSON extraction
│   ├── crawler.py              # Web crawler
│   └── grok3_api.py            # AI summarization API
├── summarize.py                # Summary generator
├── prepare_and_upload.py       # Catalog uploader
├── get_screenshoot_puppy.js    # Screenshot generator
├── links.txt                   # Input URLs
├── games.csv                   # Game metadata
├── logs/                       # Log files
├── markdown/                   # Extracted game text
├── summaries/                  # Generated summaries
├── screenshots/                # Game screenshots
└── downloaded_games/           # Downloaded game files
```

## Requirements
- Python 3.8+
- Node.js (for screenshot generation)
- Required Python packages (see requirements.txt)
- API credentials in .env file

## Workflow
1. Controller reads URLs from links.txt
2. For each URL:
   - Downloads game files
   - Checks catalog for existing entries
   - Extracts text content
   - Generates screenshots
   - Creates summaries
3. Uploads new games to catalog 