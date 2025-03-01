# Project: Semantic Search System for Text Games

## Description
The project is a system for automatic collection, processing, and search of information about text games. Main stages of work:
1. Collecting JSON files from links
2. Converting JSON to Markdown
3. Creating structured game descriptions
4. Building a database for semantic search
5. Searching the database using transformers

## File Functions

### Main Scripts
  
- **app.py** - Flask web interface for search and results display:
  - Handles GET and POST requests
  - Uses search.py to perform semantic search
  - Displays results through index.html template

- **search.py** - Semantic search engine:
  - Uses BAAI/bge-large-en-v1.5 model via Hugging Face API
  - Converts queries to 1024-dimensional embeddings
  - Calculates cosine similarity with the database
  - Returns top-K results with similarity score
  - Supports vector normalization for improved accuracy

- **crawl.py** - Link and data processing:
  - Loads JSON data by URL
  - Converts JSON to structured Markdown:
    - Extracts headers and text from objects
    - Saves results to markdown/ with project name
    - Adds game title at the beginning of the file
  - Handles errors and returns None on failures

- **controller.py** - Main control script:
  - Orchestrates the entire processing workflow:
    1. Reading URLs from links.txt
    2. Processing through crawl.py
    3. Using js_json_extractor.py and traffic_analyzer.py as backup mechanisms for extracting text from games
    4. Generating descriptions through summarize.py
    5. Creating screenshots via get_screenshoot_puppy.js
    6. Analyzing visual style through vision_query.py
    7. Logging results in log.txt
  - Supports URL normalization
  - Handles errors and tracks failed URLs
  - Adds visual descriptions to summary files

- **process_md.py** - Database creation:
  - Generates embeddings for texts
  - Saves database to search_data.json
  process_md.py supports two modes:
--init: Creates new database from all summaries
--update: Adds new entries from controller.py

- **summarize.py** - Creating game descriptions:
  - Sends text to LLM for compression
  - Generates structured descriptions
  - Saves results to summaries/

- **detect_repetition.py** - Analysis of summaries:
  - Detection of repeating word sequences
  - Identifying LLM hallucinations

- **get_screenshoot_puppy.js** - Browser automation:
  - Creates screenshots of web pages
  - Saves in PNG and WebP formats
  - Saves results to screenshoots/

- **vision_query.py** - Image analysis:
  - Generates descriptions of games' visual style
  - Uses Gemini API
  - Adds descriptions to summary files

- **traffic_analyzer.py** - Network traffic analysis:
  - Automatic detection of game data files
  - Analyzes traffic during page loading
  - Captures and processes JSON files
  - Backup mechanism for cases when crawl.py fails

### Supporting Files
- **links.txt** - List of URLs for processing
- **search_data.json** - Search database (embeddings and metadata)
- **templates/index.html** - Web interface template
- **api_status.log** - API status log

## Project Status
- crawl.py: correctly processes links
- summarize.py: successfully creates descriptions using LLM
- process_md.py: correctly creates the database
- search.py: works correctly, performs search
- Web interface: fully functional
  - Supports semantic search
  - Displays results with similarity score
  - Handles search errors
  - Supports result formatting

## Running the Search Engine
1. Make sure all dependencies are installed
npm install
pip install -r requirements.txt

2. Generate the database:
   ```bash
   python process_md.py
   ```
3. Run the web server:
   ```bash
   python app.py
   ```
4. Open http://localhost:5000 in your browser
5. Enter a search query and view results

## Notes
- Do not open search_data.json file - it's too large
- Files in markdown and summaries folders should also not be opened due to their size
- The search_data.json database contains embeddings and metadata for search













# Using ChromaDB for CYOA Game Search

## 1. How to Use New Functions in process_md

### Basic Setup
```bash
# Install required packages
pip install chromadb openai python-dotenv

# Make sure you have DeepInfra API key in .env file
# DEEPINFRA_API_KEY=your_api_key_here
```

### Initialize Database
```bash
# Process all markdown files in summaries/ directory and create vector database
python process_md.py --init
```

### Update Database with a New Game
```bash
# Add or update a single game file
python process_md.py --update path/to/game_summary.md https://game-url.com
```

### Search for Similar Games
```bash
# Search for games matching your description
python process_md.py --search "cyberpunk game with implants and rebellion"

# For more complex queries with quotes, use single quotes outside
python process_md.py --search 'game about "mind control" in a fantasy setting'
```

### Example Search Output
```
Search Results:

1. Cyber Dystopia CYOA (Similarity: 0.87)
   URL: https://example.com/cyber_dystopia
   Preview: In this cyberpunk adventure, you navigate a world dominated by mega-corporations. Choose your implants wisely as they determine your abilities in the coming rebellion...

2. Neo Tokyo 2050 (Similarity: 0.75)
   URL: https://example.com/neo_tokyo
   Preview: A futuristic CYOA where you can augment your body with various cybernetic enhancements. The story follows the underground resistance...
``` 