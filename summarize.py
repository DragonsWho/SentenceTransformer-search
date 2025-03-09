# summarize.py

import os
import asyncio
import sys
import json
import subprocess
import pandas as pd
import logging
from fuzzywuzzy import fuzz
from urllib.parse import urlparse, unquote
from components.grok3_api import GrokAPI

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/summarize.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Константы
SENT_SEARCH_PROMPT_PATH = "prompts/Grok_for_sent_search.md"
CATALOG_PROMPT_PATH = "prompts/Grok_description_for_catalog.md"
SUMMARIES_DIR = "summaries"
CATALOG_JSON_DIR = "catalog_json"
MARKDOWN_DIR = "markdown"
CSV_PATH = "games.csv"

def load_prompt(prompt_path):
    logger.info(f"Loading prompt from {prompt_path}")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_game_text(md_path):
    logger.info(f"Loading game text from {md_path}")
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Game text file not found: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_authors_list():
    logger.info("Fetching authors list")
    try:
        result = subprocess.run(
            ["python", "components/api_authors.py"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Error getting authors list: {str(e)}")
        return ""

def get_tag_categories():
    logger.info("Fetching tag categories")
    try:
        result = subprocess.run(
            ["python", "components/api_tags.py"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Error getting tag categories: {str(e)}")
        return ""

async def run_vision_query(webp_path, max_retries=3):
    logger.info(f"Running vision query for {webp_path}")
    try:
        from controller import run_script_async
        success, output, error = await run_script_async("vision_query.py", webp_path, max_retries=max_retries)
        if success and output and not output.startswith("Visual analysis error:"):
            logger.info("Vision query successful")
            return output.strip()
        logger.error(f"Vision analysis failed: {error}")
        return None
    except Exception as e:
        logger.error(f"Error in vision query: {str(e)}")
        return None

def get_csv_hint(project_name):
    logger.info(f"Getting CSV hint for {project_name}")
    if not os.path.exists(CSV_PATH):
        logger.warning(f"CSV file not found at: {CSV_PATH}")
        return "\n\n=== CSV Hint ===\nCSV file not found."
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8')
        required_columns = ['Title', 'Author', 'Type', 'Static', 'Interactive']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            logger.warning(f"CSV is missing required columns: {missing}")
            return "\n\n=== CSV Hint ===\nCSV is missing required columns."
        project_name_normalized = unquote(project_name.lower()).replace(" ", "")
        matches = []
        for index, row in df.iterrows():
            csv_title = str(row['Title']) if pd.notna(row['Title']) else ""
            csv_url = str(row['Static']) if pd.notna(row['Static']) else ""
            csv_interactive = str(row['Interactive']) if pd.notna(row['Interactive']) else ""
            csv_title_normalized = csv_title.lower().replace(" ", "")
            url_similarity = 0
            if csv_url and csv_url != "nan":
                url_normalized = unquote(csv_url.lower()).replace(" ", "")
                url_path = urlparse(csv_url).path.rstrip('/').split('/')[-1].lower()
                url_path_normalized = unquote(url_path).replace(" ", "")
                url_similarity = max(
                    fuzz.ratio(project_name_normalized, url_normalized),
                    fuzz.ratio(project_name_normalized, url_path_normalized)
                )
            interactive_similarity = 0
            if csv_interactive and csv_interactive != "nan":
                interactive_normalized = unquote(csv_interactive.lower()).replace(" ", "")
                interactive_similarity = fuzz.ratio(project_name_normalized, interactive_normalized)
            title_similarity = fuzz.ratio(project_name_normalized, csv_title_normalized)
            max_similarity = max(title_similarity, url_similarity, interactive_similarity)
            if max_similarity >= 70:
                matches.append((row, max_similarity))
        if not matches:
            return "\n\n=== CSV Hint ===\nNo matching entries found in CSV for this project name."
        matches.sort(key=lambda x: x[1], reverse=True)
        hint = "\n\n=== CSV Hint ===\nPossible matches from CSV based on project name:\n"
        for match, similarity in matches[:3]:
            hint += (
                f"- Title: {match.get('Title', 'N/A')}, "
                f"Author: {match.get('Author', 'N/A')}, "
                f"Type: {match.get('Type', 'N/A')} (Similarity: {similarity}%)\n"
            )
        hint += (
            "\nNote: When specifying the author, use the exact name as listed above (this is their nickname). "
            "The 'Type' (SFW or NSFW) is based on visual assessment. SFW strongly indicates the absence of nudity, "
            "while NSFW suggests mature content. Rely on this classification for consistency.\n"
        )
        return hint
    except Exception as e:
        logger.error(f"Unexpected error processing CSV: {str(e)}")
        return "\n\n=== CSV Hint ===\nUnexpected error processing CSV."

async def summarize_md_file(md_file, grok_api, mode="sent_search"):
    logger.info(f"Starting summarization for {md_file} in {mode} mode")
    project_name = os.path.splitext(md_file)[0]
    md_path = os.path.join(MARKDOWN_DIR, md_file)
    webp_path = f"screenshots/{project_name}.webp"
    
    if mode == "sent_search":
        prompt_path = SENT_SEARCH_PROMPT_PATH
        output_dir = SUMMARIES_DIR
        output_path = os.path.join(output_dir, f"{project_name}.md")
    elif mode == "catalog":
        prompt_path = CATALOG_PROMPT_PATH
        output_dir = CATALOG_JSON_DIR
        output_path = os.path.join(output_dir, f"{project_name}.json")
    else:
        logger.error(f"Unknown mode: {mode}")
        raise ValueError(f"Unknown mode: {mode}")

    try:
        prompt = load_prompt(prompt_path)
        game_text = load_game_text(md_path)
    except Exception as e:
        logger.error(f"Error loading files for {md_file}: {str(e)}")
        return False

    vision_description = ""
    file_paths = []
    if os.path.exists(webp_path):
        vision_output = await run_vision_query(webp_path)
        if vision_output:
            vision_description = (
                "\n\n=== Screenshot Description (First Page) ===\n"
                f"{vision_output}\n"
                "This describes the visual style and content of the game's first page, "
                "which can be used to enhance the game's description."
            )
        file_paths.append(webp_path)  # Добавляем путь к скриншоту для отправки

    additional_data = ""
    if mode == "catalog":
        logger.info("Fetching additional data for catalog mode")
        authors_list = get_authors_list()
        tag_categories = get_tag_categories()
        if authors_list:
            additional_data += f"\n\n=== Available Authors ===\n{authors_list}\n"
        if tag_categories:
            additional_data += f"\n\n=== Available Tag Categories ===\n{tag_categories}\n"
        csv_hint = get_csv_hint(project_name)
        additional_data += csv_hint

    full_prompt = f"{prompt}{additional_data}\n\n=== Game Text ===\n{game_text}{vision_description}"
    logger.info(f"Sending prompt to Grok API for {md_file} with file: {webp_path if file_paths else 'None'}")
    
    try:
        # Передаем как текстовый промпт, так и файл скриншота
        response = grok_api.ask(full_prompt, file_paths=file_paths, timeout=120)
        if response.startswith("Error:"):
            logger.error(f"Grok 3 API failed for {md_file}: {response}")
            return False
    except Exception as e:
        logger.error(f"Exception during Grok API call: {str(e)}")
        return False

    logger.info(f"API response received: {response[:100]}...")
    os.makedirs(output_dir, exist_ok=True)
    if mode == "sent_search":
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        logger.info(f"Summary saved to {output_path}")
    elif mode == "catalog":
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response)
            logger.info(f"Catalog JSON saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving JSON for {md_file}: {e}")
            return False

    return True

async def main():
    if len(sys.argv) < 2:
        logger.error("No markdown file provided. Usage: python summarize.py <markdown_file> [--mode sent_search|catalog]")
        sys.exit(1)

    md_file = sys.argv[1]
    mode = "sent_search"
    if len(sys.argv) > 2 and sys.argv[2] == "--mode":
        if len(sys.argv) > 3:
            mode = sys.argv[3]
            if mode not in ["sent_search", "catalog"]:
                logger.error(f"Invalid mode: {mode}. Use 'sent_search' or 'catalog'")
                sys.exit(1)
        else:
            logger.error("Error: --mode requires a value (sent_search or catalog)")
            sys.exit(1)

    logger.info(f"Initializing Grok API")
    try:
        grok_api = GrokAPI(reuse_window=True, anonymous_chat=True)
    except Exception as e:
        logger.error(f"Failed to initialize Grok API: {str(e)}")
        sys.exit(1)

    logger.info(f"Processing {md_file} in {mode} mode...")
    success = await summarize_md_file(md_file, grok_api, mode=mode)
    if not success:
        logger.error(f"Failed to process {md_file}")

if __name__ == "__main__":
    asyncio.run(main())