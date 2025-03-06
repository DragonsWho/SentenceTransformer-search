import os
import asyncio
import sys
from components.grok3_api import GrokAPI

# Константы
PROMPT_PATH = "prompts/Grok_for_sent_search.md"
SUMMARIES_DIR = "summaries"
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
    from controller import run_script_async  # Импортируем из controller для переиспользования
    success, output, error = await run_script_async("vision_query.py", webp_path, max_retries=max_retries)
    if success and output and not output.startswith("Visual analysis error:"):
        return output.strip()
    print(f"Vision analysis failed for {webp_path}: {error}")
    return None

async def summarize_md_file(md_file, grok_api):
    """Обрабатывает один указанный Markdown файл через Grok 3."""
    project_name = os.path.splitext(md_file)[0]
    md_path = os.path.join(MARKDOWN_DIR, md_file)
    webp_path = f"screenshoots/{project_name}.webp"
    output_path = os.path.join(SUMMARIES_DIR, f"{project_name}.md")

    # Загружаем промпт и текст игры
    try:
        prompt = load_prompt(PROMPT_PATH)
        game_text = load_game_text(md_path)
    except Exception as e:
        print(f"Error loading files for {md_file}: {str(e)}")
        return False

    # Анализируем скриншот, если он есть
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

    # Формируем полный запрос с текстом игры
    full_prompt = f"{prompt}\n\n=== Game Text ===\n{game_text}{vision_description}"

    # Отправляем запрос через GrokAPI
    response = grok_api.ask(full_prompt, timeout=120)  # Увеличенный таймаут для большого текста
    if response.startswith("Error:"):
        print(f"Grok 3 API failed for {md_file}: {response}")
        return False

    # Сохраняем результат
    os.makedirs(SUMMARIES_DIR, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response)
    print(f"Summary saved to {output_path}")
    return True

async def main():
    """Обрабатывает один файл, указанный в аргументах командной строки."""
    if len(sys.argv) < 2:
        print("Usage: python summarize.py <markdown_file>")
        sys.exit(1)

    md_file = sys.argv[1]
    # Используем reuse_window=True и anonymous_chat=True
    grok_api = GrokAPI(reuse_window=True, anonymous_chat=True)
    
    print(f"Processing {md_file}...")
    success = await summarize_md_file(md_file, grok_api)
    if not success:
        print(f"Failed to process {md_file}")

if __name__ == "__main__":
    asyncio.run(main())