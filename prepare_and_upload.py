import os
import shutil
import subprocess
import sys
import json
import re
from pathlib import Path

# Константы
CATALOG_JSON_DIR = "catalog_json"
SCREENSHOTS_DIR = "screenshots"
NEW_GAMES_DIR = "New_Games"
PROCESSED_GAMES_DIR = "Processed_Games"
GAME_UPLOADER_SCRIPT = "GameUploader.py"

def remove_json_comments(json_text):
    """Удаляет однострочные комментарии вида // из JSON, сохраняя // в строках."""
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

def validate_and_clean_json(json_path):
    """Проверяет и очищает JSON от комментариев, возвращает оригинал и очищенный текст."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        cleaned_content = remove_json_comments(original_content)
        
        try:
            json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {json_path}: {e}")
            print("Cleaned content:")
            lines = cleaned_content.splitlines()
            for i, line in enumerate(lines, 1):
                print(f"{i:3d}: {line}")
            return None, None
        
        return original_content, cleaned_content
    except Exception as e:
        print(f"Error processing JSON {json_path}: {e}")
        return None, None

def prepare_game_files(test_mode=False):
    """Копирует JSON и скриншот в New_Games для каждой игры."""
    if not os.path.exists(CATALOG_JSON_DIR):
        print(f"Error: {CATALOG_JSON_DIR} directory not found!")
        return False

    os.makedirs(NEW_GAMES_DIR, exist_ok=True)
    json_files = [f for f in os.listdir(CATALOG_JSON_DIR) if f.endswith(".json")]
    if not json_files:
        print(f"No JSON files found in {CATALOG_JSON_DIR}")
        return False

    success = True
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
                success = False
                continue

            with open(json_dest, 'w', encoding='utf-8') as f:
                f.write(cleaned_json)
            print(f"Copied cleaned JSON: {json_file} to {NEW_GAMES_DIR}")

            with open(json_with_comments_dest, 'w', encoding='utf-8') as f:
                f.write(original_json)
            print(f"Copied JSON with comments: {project_name}_with_comments.json to {NEW_GAMES_DIR}")

            if os.path.exists(screenshot_src):
                shutil.copy2(screenshot_src, screenshot_dest)
                print(f"Copied screenshot: {project_name}.webp to {NEW_GAMES_DIR}")
            else:
                print(f"Warning: Screenshot {screenshot_src} not found for {project_name}")

        except Exception as e:
            print(f"Error preparing files for {json_file}: {e}")
            success = False

    return success

def run_game_uploader():
    """Запускает GameUploader.py."""
    if not os.path.exists(GAME_UPLOADER_SCRIPT):
        print(f"Error: {GAME_UPLOADER_SCRIPT} not found!")
        return False

    try:
        result = subprocess.run(
            [sys.executable, GAME_UPLOADER_SCRIPT],
            check=True,
            text=True,
            capture_output=True
        )
        print("GameUploader output:")
        print(result.stdout)
        if result.stderr:
            print("GameUploader errors:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {GAME_UPLOADER_SCRIPT}: {e}")
        print(f"Output: {e.output}")
        return False
    except Exception as e:
        print(f"Unexpected error running {GAME_UPLOADER_SCRIPT}: {e}")
        return False

def cleanup_catalog_json():
    """Удаляет все файлы из catalog_json после успешной обработки."""
    if os.path.exists(CATALOG_JSON_DIR):
        for file in os.listdir(CATALOG_JSON_DIR):
            file_path = os.path.join(CATALOG_JSON_DIR, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed {file} from {CATALOG_JSON_DIR}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

def move_comments_files_to_processed():
    """Переносит файлы с комментариями в Processed_Games."""
    os.makedirs(PROCESSED_GAMES_DIR, exist_ok=True)
    for file in os.listdir(NEW_GAMES_DIR):
        if file.endswith("_with_comments.json"):
            src = os.path.join(NEW_GAMES_DIR, file)
            dest = os.path.join(PROCESSED_GAMES_DIR, file)
            shutil.move(src, dest)
            print(f"Moved {file} to {PROCESSED_GAMES_DIR}")

def main():
    test_mode = "--test" in sys.argv
    print(f"Running in {'test' if test_mode else 'live'} mode")

    if not prepare_game_files(test_mode):
        print("Failed to prepare game files. Aborting.")
        sys.exit(1)

    if not test_mode:
        print("Starting GameUploader...")
        if not run_game_uploader():
            print("GameUploader failed!")
            sys.exit(1)
        print("Game uploading completed successfully!")
        
        move_comments_files_to_processed()
        cleanup_catalog_json()  # Очищаем catalog_json после успешной загрузки
    else:
        print("Test mode: Skipping GameUploader execution, file moving, and cleanup.")

if __name__ == "__main__":
    main()