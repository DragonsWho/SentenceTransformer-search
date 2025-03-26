# Static Game Processing System Documentation

## Overview
The static processing system handles offline processing of game content from image files. It performs OCR, text extraction, summarization, and catalog generation for static game content.

## Main Components

### controller_static.py
The main orchestrator that manages:
- Image processing pipeline
- OCR execution
- Text extraction and optimization
- AI-powered summarization
- Catalog generation
- Error handling and logging

### Key Functions:
1. `setup_logging()` - Configures logging system
2. `run_script()` - Executes external scripts
3. `check_prerequisites()` - Validates required files
4. `process_image_folder()` - Main processing pipeline
5. `optimize_ocr_json()` - Processes OCR output
6. `clean_json_comments()` - Sanitizes JSON output

## Supporting Components

### Core Modules:
- **static_images_processing.py** - Image preprocessing
- **components/ocr/ocr.py** - Optical Character Recognition
- **components/grok3_api.py** - AI summarization interface
- **GameUploader_static.py** - Catalog upload handler

### Input/Output Files:
- **static_links.txt** - List of game folders to process
- **prompts/** - Contains AI prompt templates:
  - Grok_ocr_to_md.md
  - Grok_for_sent_search.md  
  - Grok_description_for_catalog.md
- **logs/** - Processing logs
- **markdown/static/** - Raw OCR output
- **summaries/** - Generated game descriptions

## Workflow

1. **Initialization**:
   - Load configuration
   - Validate prerequisites
   - Setup logging

2. **Image Processing**:
   - Preprocess images
   - Run OCR on each image
   - Combine text blocks

3. **Text Enhancement**:
   - Generate Markdown from OCR
   - Create structured summaries
   - Produce catalog entries

4. **Upload**:
   - Validate catalog JSON
   - Upload to server

## Usage

```bash
python controller_static.py
```

### Input Requirements:
- `static_links.txt` with paths to game folders
- Each game folder should contain image files

### Output:
- Processed Markdown files
- Structured summaries
- Catalog JSON files
- Detailed logs

## Error Handling
The system includes comprehensive error checking:
- Missing file validation
- JSON parsing safeguards
- API call retries
- Detailed logging

## Dependencies
- Python 3.8+
- External OCR tools
- Grok API access
- Image processing libraries