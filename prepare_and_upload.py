# prepare_and_upload.py

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Константы
CATALOG_JSON_DIR = "catalog_json"
SCREENSHOTS_DIR = "screenshoots"
NEW_GAMES_DIR = "New_Games"
GAME_UPLOADER_SCRIPT = "GameUploader.py"

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
            screenshot_dest = os.path.join(NEW_GAMES_DIR, f"{project_name}.webp")

            # Копируем JSON
            shutil.copy2(json_src, json_dest)
            print(f"Copied JSON: {json_file} to {NEW_GAMES_DIR}")

            # Копируем скриншот, если он существует
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

def main():
    test_mode = "--test" in sys.argv
    print(f"Running in {'test' if test_mode else 'live'} mode")

    # Подготавливаем файлы
    if not prepare_game_files(test_mode):
        print("Failed to prepare game files. Aborting.")
        sys.exit(1)

    # Если не тестовый режим, запускаем GameUploader
    if not test_mode:
        print("Starting GameUploader...")
        if not run_game_uploader():
            print("GameUploader failed!")
            sys.exit(1)
        print("Game uploading completed successfully!")
    else:
        print("Test mode: Skipping GameUploader execution.")

if __name__ == "__main__":
    main()
