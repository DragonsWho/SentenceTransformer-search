import os
import asyncio
import sys
import json
from components.grok3_api import GrokAPI

# Константы
SENT_SEARCH_PROMPT_PATH = "prompts/Grok_for_sent_search.md"
CATALOG_PROMPT_PATH = "prompts/Grok_description_for_catalog.md"
SUMMARIES_DIR = "summaries"
CATALOG_JSON_DIR = "catalog_json"
MARKDOWN_DIR = "markdown"

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

async def run_vision_query(webp_path, max_retries=3):
    """Запускает vision_query.py для анализа скриншота."""
    from controller import run_script_async
    success, output, error = await run_script_async("vision_query.py", webp_path, max_retries=max_retries)
    if success and output and not output.startswith("Visual analysis error:"):
        return output.strip()
    print(f"Vision analysis failed for {webp_path}: {error}")
    return None

async def summarize_md_file(md_file, grok_api, mode="sent_search"):
    """Обрабатывает один Markdown файл через Grok 3 с учетом режима."""
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

    full_prompt = f"{prompt}\n\n=== Game Text ===\n{game_text}{vision_description}"
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
        # Сохраняем ответ как есть, с комментариями, без проверки валидности
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