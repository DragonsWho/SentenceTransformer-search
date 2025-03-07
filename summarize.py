import os
import asyncio
import sys
import json
import subprocess
import pandas as pd
from fuzzywuzzy import fuzz
from urllib.parse import urlsplit
from components.grok3_api import GrokAPI

# Константы
SENT_SEARCH_PROMPT_PATH = "prompts/Grok_for_sent_search.md"
CATALOG_PROMPT_PATH = "prompts/Grok_description_for_catalog.md"
SUMMARIES_DIR = "summaries"
CATALOG_JSON_DIR = "catalog_json"
MARKDOWN_DIR = "markdown"
CSV_PATH = "games.csv"  # Путь к твоему CSV-файлу

def load_prompt(prompt_path):
    """Загружает промпт из файла."""
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_game_text(md_path):
    """Загружает текст игры из .md файла."""
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Game text file not found: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_authors_list():
    """Получает список авторов из api_authors.py."""
    try:
        result = subprocess.run(
            ["python", "components/api_authors.py"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting authors list: {str(e)}")
        return ""

def get_tag_categories():
    """Получает категории тегов из api_tags.py."""
    try:
        result = subprocess.run(
            ["python", "components/api_tags.py"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting tag categories: {str(e)}")
        return ""

async def run_vision_query(webp_path, max_retries=3):
    """Запускает vision_query.py для анализа скриншота."""
    from controller import run_script_async
    success, output, error = await run_script_async("vision_query.py", webp_path, max_retries=max_retries)
    if success and output and not output.startswith("Visual analysis error:"):
        return output.strip()
    print(f"Vision analysis failed for {webp_path}: {error}")
    return None

def get_csv_hint(project_name):
    """Ищет похожие строки в CSV по Title, Static и Interactive, возвращает подсказку с Title и Author."""
    if not os.path.exists(CSV_PATH):
        print(f"CSV file not found: {CSV_PATH}")
        return ""

    try:
        # Загружаем CSV
        df = pd.read_csv(CSV_PATH)
        required_columns = ['Title', 'Author', 'Static', 'Interactive']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            print(f"CSV is missing required columns: {missing}")
            return ""

        # Нормализуем project_name
        project_name_normalized = project_name.lower().replace(" ", "")
        matches = []

        for index, row in df.iterrows():
            csv_title = str(row['Title']) if pd.notna(row['Title']) else ""
            csv_url = str(row['Static']) if pd.notna(row['Static']) else ""
            csv_interactive = str(row['Interactive']) if pd.notna(row['Interactive']) else ""
            csv_title_normalized = csv_title.lower().replace(" ", "")

            # Схожесть по Title
            title_similarity = fuzz.ratio(project_name_normalized, csv_title_normalized)

            # Схожесть по Static (последний сегмент URL)
            url_similarity = 0
            if csv_url and csv_url != "nan":
                url_path = urlsplit(csv_url).path.rstrip('/').split('/')[-1]
                url_path_normalized = url_path.lower().replace(" ", "")
                url_similarity = fuzz.ratio(project_name_normalized, url_path_normalized)

            # Схожесть по Interactive (если есть)
            interactive_similarity = 0
            if csv_interactive and csv_interactive != "nan":
                interactive_normalized = csv_interactive.lower().replace(" ", "")
                interactive_similarity = fuzz.ratio(project_name_normalized, interactive_normalized)

            # Максимальная схожесть из всех полей
            max_similarity = max(title_similarity, url_similarity, interactive_similarity)
            if max_similarity >= 80:  # Порог схожести
                matches.append((row, max_similarity))

        if not matches:
            return "\n\n=== CSV Hint ===\nNo matching entries found in CSV for this project name."

        # Сортируем по убыванию схожести и берём до 3 лучших совпадений
        matches.sort(key=lambda x: x[1], reverse=True)
        hint = "\n\n=== CSV Hint ===\nPossible matches from CSV based on project name:\n"
        for match, similarity in matches[:3]:
            hint += f"- Title: {match.get('Title', 'N/A')}, Author: {match.get('Author', 'N/A')} (Similarity: {similarity}%)\n"
        return hint

    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        return "\n\n=== CSV Hint ===\nError processing CSV."

async def summarize_md_file(md_file, grok_api, mode="sent_search"):
    """Обрабатывает один Markdown файл через Grok 3 с учетом режима."""
    project_name = os.path.splitext(md_file)[0]  # Извлекаем имя файла без .md
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
        raise ValueError(f"Unknown mode: {mode}")

    try:
        prompt = load_prompt(prompt_path)
        game_text = load_game_text(md_path)
    except Exception as e:
        print(f"Error loading files for {md_file}: {str(e)}")
        return False

    vision_description = ""
    if os.path.exists(webp_path):
        vision_output = await run_vision_query(webp_path)
        if vision_output:
            vision_description = (
                "\n\n=== Screenshot Description (First Page) ===\n"
                f"{vision_output}\n"
                "This describes the visual style and content of the game's first page, "
                "which can be used to enhance the game's description."
            )

    # Добавляем данные об авторах, тегах и CSV только для режима catalog
    additional_data = ""
    if mode == "catalog":
        print("Fetching authors, tag categories, and CSV hint for catalog mode...")
        authors_list = get_authors_list()
        tag_categories = get_tag_categories()
        
        if authors_list:
            additional_data += f"\n\n=== Available Authors ===\n{authors_list}\n"
        
        if tag_categories:
            additional_data += f"\n\n=== Available Tag Categories ===\n{tag_categories}\n"

        # Добавляем подсказку из CSV на основе имени файла
        csv_hint = get_csv_hint(project_name)
        additional_data += csv_hint

    full_prompt = f"{prompt}{additional_data}\n\n=== Game Text ===\n{game_text}{vision_description}"
    print(f"Sending prompt to Grok API for {md_file} in {mode} mode...")

    response = grok_api.ask(full_prompt, timeout=120)
    if response.startswith("Error:"):
        print(f"Grok 3 API failed for {md_file}: {response}")
        return False

    print(f"API response for {md_file}: {response[:100]}...")
    os.makedirs(output_dir, exist_ok=True)
    if mode == "sent_search":
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        print(f"Summary saved to {output_path}")
    elif mode == "catalog":
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response)
            print(f"Catalog JSON (with comments) saved to {output_path}")
            if not os.path.exists(output_path):
                print(f"Warning: File {output_path} was not created!")
        except Exception as e:
            print(f"Error saving JSON for {md_file}: {e}")
            return False

    return True

async def main():
    if len(sys.argv) < 2:
        print("Usage: python summarize.py <markdown_file> [--mode sent_search|catalog]")
        sys.exit(1)

    md_file = sys.argv[1]
    mode = "sent_search"
    if len(sys.argv) > 2 and sys.argv[2] == "--mode":
        if len(sys.argv) > 3:
            mode = sys.argv[3]
            if mode not in ["sent_search", "catalog"]:
                print(f"Invalid mode: {mode}. Use 'sent_search' or 'catalog'")
                sys.exit(1)
        else:
            print("Error: --mode requires a value (sent_search or catalog)")
            sys.exit(1)

    grok_api = GrokAPI(reuse_window=True, anonymous_chat=True)
    print(f"Processing {md_file} in {mode} mode...")
    success = await summarize_md_file(md_file, grok_api, mode=mode)
    if not success:
        print(f"Failed to process {md_file}")

if __name__ == "__main__":
    asyncio.run(main())