# controller_static.py

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
        
        logger.info(f"Running command: {' '.join(command)}")
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
        
        logger.info(f"Script {script_name} completed successfully. Output: {output}")
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
    
    if not os.path.exists("GameUploader_static.py"):
        logger.error("Required script not found: GameUploader_static.py")
        return False
    
    return True

def load_prompt(prompt_path):
    logger.info(f"Loading prompt from {prompt_path}")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def calculate_center(coordinates):
    x_coords = [coord[0] for coord in coordinates]
    y_coords = [coord[1] for coord in coordinates]
    center_x = sum(x_coords) / 4
    center_y = sum(y_coords) / 4
    return [int(center_x), int(center_y)]

def optimize_ocr_json(ocr_data):
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
    return json.dumps(optimized_data, ensure_ascii=False)

def process_image_folder(folder_path, output_dir="markdown/static"):
    folder_path = Path(folder_path).resolve()
    if not folder_path.exists() or not folder_path.is_dir():
        logger.error(f"Folder does not exist or is not a directory: {folder_path}")
        return False
    
    game_name = folder_path.name
    ocr_raw_dir = folder_path / "ocr_raw"
    ocr_md_dir = folder_path / "ocr_markdown_pages"
    summaries_dir = folder_path / "summaries"
    os.makedirs(ocr_raw_dir, exist_ok=True)
    os.makedirs(ocr_md_dir, exist_ok=True)
    os.makedirs(summaries_dir, exist_ok=True)
    
    try:
        grok_api = GrokAPI(reuse_window=True, anonymous_chat=True)
    except Exception as e:
        logger.error(f"Failed to initialize Grok API: {str(e)}")
        return False
    
    ocr_prompt_path = "prompts/Grok_ocr_to_md.md"
    sent_search_prompt_path = "prompts/Grok_for_sent_search.md"
    catalog_prompt_path = "prompts/Grok_description_for_catalog.md"
    try:
        ocr_prompt = load_prompt(ocr_prompt_path)
        sent_search_prompt = load_prompt(sent_search_prompt_path)
        catalog_prompt = load_prompt(catalog_prompt_path)
    except Exception as e:
        logger.error(f"Error loading prompts: {str(e)}")
        return False
    
    image_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
    images = [f for f in folder_path.iterdir() if f.suffix.lower() in image_extensions]
    if not images:
        logger.warning(f"No images found in folder: {folder_path}")
        return False
    
    images = sorted(images)
    logger.info(f"Found {len(images)} images in folder: {folder_path}")
    
    # Проверка наличия OCR raw файлов
    ocr_raw_files = {f.stem: f for f in ocr_raw_dir.iterdir() if f.suffix == ".json"}
    expected_ocr_raw = {img.stem: f"{img.stem}_ocr.json" for img in images}
    ocr_raw_complete = all(
        name in ocr_raw_files and os.path.getsize(ocr_raw_files[name]) > 0 
        for name in expected_ocr_raw
    )
    
    combined_text_blocks = []
    
    if not ocr_raw_complete:
        logger.info(f"OCR raw data incomplete or missing for some images in {folder_path}")
        for i, image_path in enumerate(images, 1):
            ocr_output_file = ocr_raw_dir / f"{image_path.stem}_ocr.json"
            if (image_path.stem not in ocr_raw_files or 
                not os.path.exists(ocr_output_file) or 
                os.path.getsize(ocr_output_file) == 0):
                logger.info(f"Running OCR on image {i}/{len(images)}: {image_path}")
                success, output, error = run_script("components/ocr/ocr.py", [str(image_path), str(ocr_output_file)])
                if not success:
                    logger.error(f"OCR failed for {image_path}: {error}")
                    continue
            try:
                with open(ocr_output_file, "r", encoding="utf-8") as f:
                    ocr_data = json.load(f)
                for block in ocr_data.get("text_blocks", []):
                    block["source_image"] = str(image_path.name)
                    combined_text_blocks.append(block)
            except Exception as e:
                logger.error(f"Error loading OCR JSON {ocr_output_file}: {str(e)}")
                continue
    else:
        logger.info(f"All OCR raw files exist and are valid in {ocr_raw_dir}. Skipping OCR generation.")
        for image_path in images:
            ocr_output_file = ocr_raw_dir / f"{image_path.stem}_ocr.json"
            try:
                with open(ocr_output_file, "r", encoding="utf-8") as f:
                    ocr_data = json.load(f)
                for block in ocr_data.get("text_blocks", []):
                    block["source_image"] = str(image_path.name)
                    combined_text_blocks.append(block)
            except Exception as e:
                logger.error(f"Error loading existing OCR JSON {ocr_output_file}: {str(e)}")
                continue
    
    if not combined_text_blocks:
        logger.error(f"No text blocks extracted for folder: {folder_path}")
        return False
    
    # Проверка наличия OCR Markdown файлов
    ocr_md_files = {f.stem: f for f in ocr_md_dir.iterdir() if f.suffix == ".md"}
    expected_ocr_md = {img.stem: f"{img.stem}.md" for img in images}
    ocr_md_complete = all(
        name in ocr_md_files and os.path.getsize(ocr_md_files[name]) > 0 
        for name in expected_ocr_md
    )
    
    if not ocr_md_complete:
        logger.info(f"OCR Markdown files incomplete or missing in {folder_path}")
        for i, image_path in enumerate(images, 1):
            md_output_file = ocr_md_dir / f"{image_path.stem}.md"
            if (image_path.stem not in ocr_md_files or 
                not os.path.exists(md_output_file) or 
                os.path.getsize(md_output_file) == 0):
                ocr_output_file = ocr_raw_dir / f"{image_path.stem}_ocr.json"
                try:
                    with open(ocr_output_file, "r", encoding="utf-8") as f:
                        ocr_data = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading OCR JSON for Markdown generation {ocr_output_file}: {str(e)}")
                    continue
                
                optimized_json = optimize_ocr_json(ocr_data)
                full_prompt = f"{ocr_prompt}\n\n=== OCR JSON ===\n{optimized_json}"
                logger.info(f"Sending optimized prompt to Grok API for {image_path.name}")
                
                try:
                    response = grok_api.ask(full_prompt, timeout=120)
                    if response.startswith("Error:"):
                        logger.error(f"Grok API failed for {image_path.name}: {response}")
                        continue
                    with open(md_output_file, "w", encoding="utf-8") as f:
                        f.write(response)
                    logger.info(f"Markdown from Grok API saved to {md_output_file}")
                except Exception as e:
                    logger.error(f"Exception during Grok API call for {image_path.name}: {str(e)}")
                    continue
            else:
                logger.info(f"Using existing Markdown file for {image_path}: {md_output_file}")
    else:
        logger.info(f"All OCR Markdown files exist and are valid in {ocr_md_dir}. Skipping Markdown generation.")
    
    # Сохранение объединенного Markdown из OCR raw
    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, f"{game_name}.md")
    if not os.path.exists(md_path) or os.path.getsize(md_path) == 0:
        md_content = [f"Game Folder: {folder_path}\n\nPossible title: {game_name.replace('_', ' ')}\n"]
        for block in combined_text_blocks:
            md_content.append(f"### From {block['source_image']}\n{block['text']}\n")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))
        logger.info(f"Raw OCR Markdown saved to {md_path}")
    else:
        logger.info(f"Raw OCR Markdown already exists at {md_path}. Skipping generation.")
    
    md_files = [f for f in ocr_md_dir.iterdir() if f.suffix == ".md"]
    if not md_files:
        logger.error(f"No enhanced Markdown files found in {ocr_md_dir}")
        return False
    
    combined_md_content = ""
    for md_file in sorted(md_files):
        with open(md_file, "r", encoding="utf-8") as f:
            combined_md_content += f"\n\n=== {md_file.name} ===\n{f.read()}"
    
    # Проверка наличия файлов в summaries
    sent_search_output_path = summaries_dir / f"{game_name}_sent_search.md"
    catalog_output_path = summaries_dir / f"{game_name}_catalog.json"
    summaries_complete = (
        os.path.exists(sent_search_output_path) and os.path.getsize(sent_search_output_path) > 0 and
        os.path.exists(catalog_output_path) and os.path.getsize(catalog_output_path) > 0
    )
    
    if not summaries_complete:
        logger.info(f"Summaries incomplete or missing in {summaries_dir}")
        # Генерация sent_search
        if not os.path.exists(sent_search_output_path) or os.path.getsize(sent_search_output_path) == 0:
            sent_search_full_prompt = f"{sent_search_prompt}\n\n=== Combined Enhanced Game Text ===\n{combined_md_content}"
            logger.info(f"Sending sent_search prompt to Grok API for {game_name}")
            try:
                sent_search_response = grok_api.ask(sent_search_full_prompt, timeout=120)
                if sent_search_response.startswith("Error:"):
                    logger.error(f"Grok API failed for sent_search on {game_name}: {sent_search_response}")
                else:
                    with open(sent_search_output_path, "w", encoding="utf-8") as f:
                        f.write(sent_search_response)
                    logger.info(f"Sent_search summary saved to {sent_search_output_path}")
            except Exception as e:
                logger.error(f"Exception during sent_search Grok API call for {game_name}: {str(e)}")
        else:
            logger.info(f"Sent_search summary already exists at {sent_search_output_path}. Skipping generation.")
        
        # Генерация catalog
        if not os.path.exists(catalog_output_path) or os.path.getsize(catalog_output_path) == 0:
            catalog_full_prompt = f"{catalog_prompt}\n\n=== Combined Enhanced Game Text ===\n{combined_md_content}"
            logger.info(f"Sending catalog prompt to Grok API for {game_name}")
            try:
                catalog_response = grok_api.ask(catalog_full_prompt, timeout=120)
                if catalog_response.startswith("Error:"):
                    logger.error(f"Grok API failed for catalog on {game_name}: {catalog_response}")
                else:
                    with open(catalog_output_path, "w", encoding="utf-8") as f:
                        f.write(catalog_response)
                    logger.info(f"Catalog JSON saved to {catalog_output_path}")
            except Exception as e:
                logger.error(f"Exception during catalog Grok API call for {game_name}: {str(e)}")
        else:
            logger.info(f"Catalog JSON already exists at {catalog_output_path}. Skipping generation.")
    else:
        logger.info(f"All summary files exist and are valid in {summaries_dir}. Skipping summary generation.")
    
    # Отправка на сервер независимо от наличия summaries
    logger.info(f"Uploading game {game_name} using GameUploader_static.py")
    success, output, error = run_script("GameUploader_static.py", [str(catalog_output_path), str(folder_path)])
    if success:
        logger.info(f"Successfully uploaded game {game_name}: {output}")
    else:
        logger.error(f"Failed to upload game {game_name}: {error}")
    
    logger.info(f"Processed folder: {folder_path}")
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