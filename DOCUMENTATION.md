# Project Documentation

## Overview
This is a web scraping and processing system designed to:
1. Download interactive CYOA games from various sources
2. Extract and process their content
3. Generate summaries and metadata
4. Upload processed games to a catalog

## Main Components

### 1. Controller (controller.py)
The main orchestrator that coordinates all other components.

**Key Functions:**
- `main_async()` - Main processing loop
- `run_script()` - Runs Python/Node scripts
- `run_script_async()` - Async version of script runner
- `create_screenshot()` - Generates game screenshots
- `check_prerequisites()` - Validates required files/directories

**Usage:**
```
python controller.py [--force-screenshots] [--test]
```

### 2. Game Checker (game_checker.py)
Manages game catalog and checks for existing games.

**Key Features:**
- Authentication with API
- Loading existing games
- Game existence checking
- URL normalization

**Usage:**
```python
checker = GameChecker()
checker.login()
checker.load_existing_games()
exists = checker.game_exists(url)
```

### 3. Project Downloader (project_downloader.py)
Downloads game projects and their resources.

**Key Features:**
- Concurrent downloads
- Resource discovery
- Metadata tracking
- ETag-based caching

**Usage:**
```python
completed, downloaded, failed = crawl_and_download(url, output_path)
```

### 4. Summarizer (summarize.py)
Generates summaries and catalog entries from game content.

**Modes:**
- `sent_search` - Creates searchable summaries
- `catalog` - Generates catalog JSON entries

**Usage:**
```
python summarize.py <markdown_file> [--mode sent_search|catalog]
```

## Supporting Components

### 1. Traffic Analyzer
Analyzes network traffic to extract game content.

### 2. JS JSON Extractor
Extracts JSON data from JavaScript files.

### 3. Crawler
Basic web crawler for fetching game content.

### 4. Vision Processing
Handles screenshot generation and analysis.

## File Structure

```
.
├── controller.py               # Main controller
├── components/
│   ├── game_checker.py         # Game catalog management
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

## Workflow

1. Controller reads URLs from links.txt
2. For each URL:
   - Downloads game files using project_downloader
   - Checks if game exists in catalog using game_checker
   - Extracts text content using crawler/js_json_extractor/traffic_analyzer
   - Generates screenshots
   - Creates summaries using summarize.py
3. Uploads new games to catalog using prepare_and_upload.py
 