import os
import shutil
import subprocess
import sys
import json
import re
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/prepare_and_upload.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
CATALOG_JSON_DIR = "catalog_json"
SCREENSHOTS_DIR = "screenshots"
NEW_GAMES_DIR = "New_Games"
PROCESSED_GAMES_DIR = "Processed_Games"
GAME_UPLOADER_SCRIPT = "GameUploader.py"

def remove_json_comments(json_text):
    """Remove single-line comments (//) from JSON, preserving them in strings."""
    lines = json_text.splitlines()
    cleaned_lines = []
    in_string = False
    i = 0

    while i < len(lines):
        line = lines[i]
        cleaned_line = ""
        j = 0

        while j < len(line):
            if line[j] == '"' and (j == 0 or line[j-1] != '\\'):
                in_string = not in_string
                cleaned_line += line[j]
                j += 1
            elif not in_string and j + 1 < len(line) and line[j:j+2] == '//':
                break
            else:
                cleaned_line += line[j]
                j += 1

        cleaned_line = cleaned_line.rstrip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
        i += 1

    return '\n'.join(cleaned_lines)

def strip_markdown_wrappers(json_text):
    """Strip Markdown code block wrappers (e.g., ```json and ```) from JSON text."""
    lines = json_text.splitlines()
    cleaned_lines = []

    # Skip lines that are part of Markdown code block markers
    for line in lines:
        stripped_line = line.strip()
        if stripped_line == "```json" or stripped_line == "```":
            continue
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def validate_and_clean_json(json_path):
    """Validate and clean JSON from comments and Markdown wrappers, return original and cleaned text."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # First strip Markdown wrappers
        content_no_markdown = strip_markdown_wrappers(original_content)
        # Then remove comments
        cleaned_content = remove_json_comments(content_no_markdown)

        # Validate the cleaned content
        try:
            json.loads(cleaned_content)
            logger.info(f"JSON validated successfully after cleaning: {json_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_path} after cleaning: {e}")
            logger.debug(f"Cleaned content:\n{cleaned_content}")
            return None, None

        return original_content, cleaned_content
    except Exception as e:
        logger.error(f"Error processing JSON {json_path}: {e}")
        return None, None

def load_base64_image(project_name):
    """Load base64 image string from file if it exists."""
    base64_path = os.path.join(SCREENSHOTS_DIR, f"{project_name}_base64.txt")
    if os.path.exists(base64_path):
        try:
            with open(base64_path, 'r', encoding='utf-8') as f:
                base64_string = f.read().strip()
            logger.info(f"Loaded base64 image from: {base64_path}")
            return base64_string
        except Exception as e:
            logger.error(f"Error loading base64 image {base64_path}: {e}")
            return None
    else:
        logger.warning(f"Base64 image not found: {base64_path}")
        return None

def prepare_game_files(test_mode=False):
    """Copy JSON, screenshot, and base64 to New_Games for each game, skipping invalid files."""
    if not os.path.exists(CATALOG_JSON_DIR):
        logger.error(f"Directory not found: {CATALOG_JSON_DIR}")
        return False

    os.makedirs(NEW_GAMES_DIR, exist_ok=True)
    json_files = [f for f in os.listdir(CATALOG_JSON_DIR) if f.endswith(".json")]
    if not json_files:
        logger.warning(f"No JSON files found in {CATALOG_JSON_DIR}")
        return False

    logger.info(f"Found {len(json_files)} JSON files to process")
    success_count = 0
    for json_file in json_files:
        try:
            project_name = os.path.splitext(json_file)[0]
            json_src = os.path.join(CATALOG_JSON_DIR, json_file)
            screenshot_src = os.path.join(SCREENSHOTS_DIR, f"{project_name}.webp")
            json_dest = os.path.join(NEW_GAMES_DIR, json_file)
            json_with_comments_dest = os.path.join(NEW_GAMES_DIR, f"{project_name}_with_comments.json")
            screenshot_dest = os.path.join(NEW_GAMES_DIR, f"{project_name}.webp")

            original_json, cleaned_json = validate_and_clean_json(json_src)
            if cleaned_json is None:
                logger.warning(f"Skipping {json_file} due to invalid JSON after cleaning")
                continue

            # Load JSON data to modify it
            game_data = json.loads(cleaned_json)
            
            # Add base64 image if available
            base64_image = load_base64_image(project_name)
            if base64_image:
                game_data['image_base64'] = base64_image

            # Save modified JSON
            with open(json_dest, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Copied cleaned and modified JSON: {json_file} to {NEW_GAMES_DIR}")

            with open(json_with_comments_dest, 'w', encoding='utf-8') as f:
                f.write(original_json)
            logger.info(f"Copied JSON with comments: {project_name}_with_comments.json to {NEW_GAMES_DIR}")

            if os.path.exists(screenshot_src):
                shutil.copy2(screenshot_src, screenshot_dest)
                logger.info(f"Copied screenshot: {project_name}.webp to {NEW_GAMES_DIR}")
            else:
                logger.warning(f"Screenshot not found: {screenshot_src}")

            success_count += 1
        except Exception as e:
            logger.error(f"Error preparing files for {json_file}: {e}")
            continue  # Continue processing other files

    if success_count == 0:
        logger.error("No files were successfully prepared")
        return False
    logger.info(f"Successfully prepared {success_count} out of {len(json_files)} files")
    return True

def run_game_uploader():
    """Run GameUploader.py."""
    if not os.path.exists(GAME_UPLOADER_SCRIPT):
        logger.error(f"Script not found: {GAME_UPLOADER_SCRIPT}")
        return False

    try:
        logger.info("Starting GameUploader.py")
        result = subprocess.run(
            [sys.executable, GAME_UPLOADER_SCRIPT],
            check=True,
            text=True,
            capture_output=True
        )
        logger.info("GameUploader.py completed successfully")
        logger.debug(f"Output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"GameUploader.py stderr:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"GameUploader.py failed with exit code {e.returncode}: {e.output}")
        logger.debug(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running GameUploader.py: {e}")
        return False

def cleanup_catalog_json():
    """Remove all files from catalog_json after successful processing."""
    if os.path.exists(CATALOG_JSON_DIR):
        for file in os.listdir(CATALOG_JSON_DIR):
            file_path = os.path.join(CATALOG_JSON_DIR, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed {file} from {CATALOG_JSON_DIR}")
            except Exception as e:
                logger.error(f"Error removing {file_path}: {e}")

def move_comments_files_to_processed():
    """Move files with comments to Processed_Games."""
    os.makedirs(PROCESSED_GAMES_DIR, exist_ok=True)
    for file in os.listdir(NEW_GAMES_DIR):
        if file.endswith("_with_comments.json"):
            src = os.path.join(NEW_GAMES_DIR, file)
            dest = os.path.join(PROCESSED_GAMES_DIR, file)
            shutil.move(src, dest)
            logger.info(f"Moved {file} to {PROCESSED_GAMES_DIR}")

def main():
    test_mode = "--test" in sys.argv
    logger.info(f"Running in {'test' if test_mode else 'live'} mode")

    if not prepare_game_files(test_mode):
        logger.error("Failed to prepare game files. Aborting.")
        sys.exit(1)

    if not test_mode:
        logger.info("Starting game upload process")
        if not run_game_uploader():
            logger.error("GameUploader failed. Aborting.")
            sys.exit(1)
        logger.info("Game uploading completed successfully")

        move_comments_files_to_processed()
        cleanup_catalog_json()
    else:
        logger.info("Test mode: Skipping upload, file moving, and cleanup.")

if __name__ == "__main__":
    main()