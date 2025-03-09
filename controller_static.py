import os
import sys
import datetime
import subprocess
import logging
import json
from pathlib import Path
from components.grok3_api import GrokAPI

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(f"logs/static_process_{date_str}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("Static process started")
    return logging.getLogger()

def run_script(script_name, args=None):
    if not os.path.exists(script_name):
        logger.error(f"Script file not found: {script_name}")
        return False, "", f"File not found: {script_name}"
    
    try:
        command = [sys.executable, script_name]
        if args:
            command.extend(args if isinstance(args, list) else [args])
        
        logger.info(f"Выполняется команда: {' '.join(command)}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        output, error = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Script {script_name} returned non-zero exit code: {process.returncode}")
            logger.error(f"Output: {output}")
            logger.error(f"Error: {error}")
            return False, output, error
        
        logger.info(f"Script {script_name} успешно выполнен. Output: {output}")
        return True, output, error
    
    except Exception as e:
        logger.error(f"Error running script {script_name}: {str(e)}")
        return False, "", str(e)

def check_prerequisites():
    if not os.path.exists("static_links.txt"):
        logger.error("static_links.txt file not found!")
        return False
    
    with open("static_links.txt", "r", encoding="utf-8") as f:
        folders = [line.strip() for line in f if line.strip()]
        if not folders:
            logger.error("static_links.txt file is empty!")
            return False
    
    if not os.path.exists("components/ocr/ocr.py"):
        logger.error("Required script not found: components/ocr/ocr.py")
        return False
    
    if not os.path.exists("prompts/Grok_ocr_to_md.md"):
        logger.error("Prompt file not found: prompts/Grok_ocr_to_md.md")
        return False
    
    return True

def load_prompt(prompt_path):
    logger.info(f"Loading prompt from {prompt_path}")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def calculate_center(coordinates):
    """Вычисляет центральную точку из четырех углов"""
    x_coords = [coord[0] for coord in coordinates]
    y_coords = [coord[1] for coord in coordinates]
    center_x = sum(x_coords) / 4
    center_y = sum(y_coords) / 4
    return [int(center_x), int(center_y)]

def optimize_ocr_json(ocr_data):
    """Оптимизирует JSON для API: заменяет координаты на центр и убирает отступы"""
    optimized_data = {
        "image_path": ocr_data["image_path"],
        "text_blocks": []
    }
    for block in ocr_data.get("text_blocks", []):
        optimized_block = {
            "text": block["text"],
            "center": calculate_center(block["coordinates"])
        }
        optimized_data["text_blocks"].append(optimized_block)
    return json.dumps(optimized_data, ensure_ascii=False)  # Сжатый формат без отступов

def process_image_folder(folder_path, output_dir="markdown/static"):
    folder_path = Path(folder_path).resolve()
    if not folder_path.exists() or not folder_path.is_dir():
        logger.error(f"Folder does not exist or is not a directory: {folder_path}")
        return False
    
    game_name = folder_path.name
    ocr_raw_dir = folder_path / "ocr_raw"
    ocr_md_dir = folder_path / "ocr_markdown_pages"
    os.makedirs(ocr_raw_dir, exist_ok=True)
    os.makedirs(ocr_md_dir, exist_ok=True)
    
    # Инициализируем GrokAPI
    try:
        grok_api = GrokAPI(reuse_window=True, anonymous_chat=True)
    except Exception as e:
        logger.error(f"Failed to initialize Grok API: {str(e)}")
        return False
    
    # Загружаем промпт
    prompt_path = "prompts/Grok_ocr_to_md.md"
    try:
        prompt = load_prompt(prompt_path)
    except Exception as e:
        logger.error(f"Error loading prompt: {str(e)}")
        return False
    
    # Step 1: OCR all images in the folder
    image_extensions = (".jpg", ".jpeg", ".png", ".bmp")
    images = [f for f in folder_path.iterdir() if f.suffix.lower() in image_extensions]
    if not images:
        logger.warning(f"No images found in folder: {folder_path}")
        return False
    
    logger.info(f"Processing {len(images)} images in folder: {folder_path}")
    combined_text_blocks = []
    
    for i, image_path in enumerate(sorted(images), 1):
        logger.info(f"Running OCR on image {i}/{len(images)}: {image_path}")
        ocr_output_file = ocr_raw_dir / f"{image_path.stem}_ocr.json"
        success, output, error = run_script("components/ocr/ocr.py", [str(image_path), str(ocr_output_file)])
        if not success:
            logger.error(f"OCR failed for {image_path}: {error}")
            continue
        
        # Загружаем сырые данные OCR
        try:
            with open(ocr_output_file, "r", encoding="utf-8") as f:
                ocr_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading OCR JSON {ocr_output_file}: {str(e)}")
            continue
        
        # Оптимизируем JSON для API
        optimized_json = optimize_ocr_json(ocr_data)
        
        # Формируем запрос для Grok API
        full_prompt = f"{prompt}\n\n=== OCR JSON ===\n{optimized_json}"
        logger.info(f"Sending optimized prompt to Grok API for {image_path.name}")
        
        # Отправляем запрос в Grok API
        try:
            response = grok_api.ask(full_prompt, timeout=120)
            if response.startswith("Error:"):
                logger.error(f"Grok API failed for {image_path.name}: {response}")
                continue
        except Exception as e:
            logger.error(f"Exception during Grok API call for {image_path.name}: {str(e)}")
            continue
        
        # Сохраняем результат в ocr_markdown_pages
        md_output_file = ocr_md_dir / f"{image_path.stem}.md"
        try:
            with open(md_output_file, "w", encoding="utf-8") as f:
                f.write(response)
            logger.info(f"Markdown from Grok API saved to {md_output_file}")
        except Exception as e:
            logger.error(f"Error saving Markdown for {image_path.name}: {str(e)}")
            continue
        
        # Добавляем сырые данные в combined_text_blocks для общего Markdown
        for block in ocr_data.get("text_blocks", []):
            block["source_image"] = str(image_path.name)
            combined_text_blocks.append(block)
    
    if not combined_text_blocks:
        logger.error(f"No text blocks extracted for folder: {folder_path}")
        return False
    
    # Step 2: Convert raw OCR to Markdown
    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, f"{game_name}.md")
    md_content = [f"Game Folder: {folder_path}\n\nPossible title: {game_name.replace('_', ' ')}\n"]
    
    for block in combined_text_blocks:
        md_content.append(f"### From {block['source_image']}\n{block['text']}\n")
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
    
    logger.info(f"Raw OCR Markdown saved to {md_path}")
    logger.info(f"Raw OCR data saved in {ocr_raw_dir}")
    logger.info(f"Grok-processed Markdown saved in {ocr_md_dir}")
    return True

def main():
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Aborting.")
        sys.exit(1)
    
    with open("static_links.txt", "r", encoding="utf-8") as f:
        folders = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Loaded {len(folders)} folders from static_links.txt")
    
    processed_folders = []
    failed_folders = []
    
    for i, folder in enumerate(folders, 1):
        logger.info(f"Processing folder {i}/{len(folders)}: {folder}")
        success = process_image_folder(folder)
        if success:
            processed_folders.append(folder)
        else:
            failed_folders.append(folder)
    
    # Generate report
    timestamp = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    report = [
        f"\n{timestamp} Static Processing Summary:",
        f"  Total folders processed: {len(folders)}",
        f"  Successfully processed: {len(processed_folders)}",
        f"  Failed to process: {len(failed_folders)}",
    ]
    
    if failed_folders:
        report.append("  Failed folders:")
        report.extend(f"    - {folder}" for folder in failed_folders)
    
    if processed_folders:
        report.append("  Successfully processed folders:")
        report.extend(f"    - {folder}" for folder in processed_folders)
    
    for line in report:
        logger.info(line)
    
    with open("log.txt", "a", encoding="utf-8") as log_file:
        for line in report:
            log_file.write(f"{line}\n")
    
    print("\n=== Static Processing Report ===")
    for line in report:
        print(line)
    
    logger.info("Static process completed")

if __name__ == "__main__":
    logger = setup_logging()
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception in static process: {str(e)}")
        sys.exit(1)