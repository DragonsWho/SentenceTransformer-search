# components/game_text_extractor.py

import os
import json
import re
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/game_text_extractor.log"),
        logging.StreamHandler()
    ]
)

def json_to_md(data):
    """Конвертирует JSON в Markdown."""
    md_content = []
    if 'rows' in data:
        for row in data['rows']:
            if 'titleText' in row:
                md_content.append(f"## {row.get('title', '')}\n")
                md_content.append(f"{row['titleText']}\n")
            if 'objects' in row:
                for obj in row['objects']:
                    if 'title' in obj:
                        md_content.append(f"### {obj['title']}\n")
                    if 'text' in obj:
                        md_content.append(f"{obj['text']}\n")
    return "\n".join(md_content)

def extract_json_from_js(js_content):
    """Извлекает JSON из .js файла."""
    pattern = re.compile(r'Store\(\{state:\{app:(.*?)\},getters:\{checkRequireds', re.DOTALL)
    match = pattern.search(js_content)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from JS: {e}")
            return None
    return None

def extract_game_text(downloaded_files, output_dir="markdown"):
    """Извлекает текст из .json или .js файлов."""
    os.makedirs(output_dir, exist_ok=True)
    json_file = None
    js_files = []

    # Разделяем файлы на .json и .js
    for file_path in downloaded_files:
        if file_path.endswith('.json'):
            json_file = file_path
        elif file_path.endswith('.js'):
            js_files.append(file_path)

    project_name = None
    md_content = None

    # Проверяем project.json
    if json_file and os.path.basename(json_file) == 'project.json':
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            md_content = json_to_md(data)
            project_name = os.path.basename(os.path.dirname(json_file))
            logging.info(f"Extracted text from {json_file}")
        except Exception as e:
            logging.error(f"Error processing {json_file}: {e}")

    # Если json нет или не удалось извлечь, проверяем .js файлы
    if not md_content and js_files:
        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    js_content = f.read()
                data = extract_json_from_js(js_content)
                if data:
                    md_content = json_to_md(data)
                    project_name = os.path.basename(os.path.dirname(js_file))
                    logging.info(f"Extracted text from {js_file}")
                    break
            except Exception as e:
                logging.error(f"Error processing {js_file}: {e}")

    # Сохраняем результат
    if md_content and project_name:
        md_path = os.path.join(output_dir, f"{project_name}.md")
        game_url = os.path.dirname(downloaded_files[0])  # Предполагаем, что это корень игры
        game_title = project_name.replace('_', ' ')
        full_content = f"Game URL: {game_url}/\n\nPossible title: {game_title}\n\n{md_content}"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        logging.info(f"Saved Markdown to {md_path}")
        return md_path
    else:
        logging.warning("No text extracted from JSON or JS files")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python game_text_extractor.py <downloaded_folder>")
        sys.exit(1)
    folder = sys.argv[1]
    files = [os.path.join(folder, f) for f in os.listdir(folder)]
    result = extract_game_text(files)
    if result:
        print(f"Text extracted and saved to: {result}")
    else:
        print("Failed to extract text")