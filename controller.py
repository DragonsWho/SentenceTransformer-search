import subprocess
import sys
import datetime
import os
import time
import logging
import traceback
from components.traffic_analyzer import TrafficAnalyzer
from components.js_json_extractor import extract_js_json
from components.crawler import crawl_url

# Настройка системы логирования
def setup_logging():
    # Создаем директорию для логов если её нет
    os.makedirs("logs", exist_ok=True)
    
    # Текущая дата для имени файла
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Настройка логирования в файл и консоль
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(f"logs/process_{date_str}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Логируем начало процесса
    logging.info("="*50)
    logging.info("Process started")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Current directory: {os.getcwd()}")
    logging.info("="*50)
    
    return logging.getLogger()

def run_script(script_name, args=None):
    """
    Запускает внешний скрипт с расширенным логированием и проверками
    
    Args:
        script_name: Имя скрипта для запуска
        args: Строка аргументов для скрипта
        
    Returns:
        tuple: (success, output, error)
    """
    logger.info(f"Running script: {script_name} with args: {args}")
    
    # Проверка существования файла
    if not os.path.exists(script_name):
        logger.error(f"Script file not found: {script_name}")
        return False, "", f"File not found: {script_name}"
    
    try:
        # Use node for .js files, python for .py files
        if script_name.endswith('.js'):
            command = ['node', script_name]
        else:
            command = [sys.executable, script_name]
            
        if args:
            command.extend(args.split())
            
        # Логируем полную команду
        logger.debug(f"Command: {' '.join(command)}")
        
        # Запускаем процесс с таймаутом
        start_time = time.time()
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Захватываем вывод в реальном времени с таймаутом 
        output_lines = []
        error_lines = []
        
        # Функция для логирования и сохранения вывода
        def process_output(stream, prefix, output_list):
            for line in stream:
                line = line.strip()
                if line:
                    logger.debug(f"{prefix}: {line}")
                    print(f"{prefix}: {line}")
                    output_list.append(line)
        
        # Обработка stdout
        process_output(process.stdout, "OUTPUT", output_lines)
        
        # Обработка stderr
        process_output(process.stderr, "ERROR", error_lines)
        
        # Ожидаем завершения процесса
        process.wait()
        
        execution_time = time.time() - start_time
        logger.info(f"Script execution time: {execution_time:.2f} seconds")
        
        # Анализ результата
        output = "\n".join(output_lines)
        error = "\n".join(error_lines)
        
        if process.returncode != 0:
            logger.error(f"Script returned non-zero exit code: {process.returncode}")
            logger.error(f"Error output: {error}")
            return False, output, error
            
        logger.info(f"Script completed successfully: {script_name}")
        return True, output, error
    
    except subprocess.TimeoutExpired:
        logger.error(f"Script timed out: {script_name}")
        return False, "", "Timeout expired"
    except Exception as e:
        logger.error(f"Error running script: {script_name}")
        logger.error(f"Exception: {str(e)}")
        logger.error(traceback.format_exc())
        return False, "", str(e)

def check_prerequisites():
    """Проверка необходимых условий перед запуском"""
    prerequisites_met = True
    
    # Проверка наличия необходимых директорий
    for directory in ["markdown", "summaries", "screenshoots"]:
        if not os.path.exists(directory):
            logger.info(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)
    
    # Проверка наличия файла с ссылками
    if not os.path.exists("links.txt"):
        logger.error("links.txt file not found!")
        prerequisites_met = False
    else:
        with open("links.txt", "r") as f:
            urls = [line.strip() for line in f if line.strip()]
            if not urls:
                logger.error("links.txt file is empty!")
                prerequisites_met = False
            else:
                logger.info(f"Found {len(urls)} URLs in links.txt")
    
    # Проверка наличия Node.js для скриптов .js
    try:
        result = subprocess.run(["node", "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        if result.returncode == 0:
            logger.info(f"Node.js version: {result.stdout.strip()}")
        else:
            logger.error("Node.js not found! Required for JavaScript scripts.")
            prerequisites_met = False
    except:
        logger.error("Error checking Node.js. Make sure it's installed.")
        prerequisites_met = False
    
    return prerequisites_met

def main():
    # Проверка всех предварительных условий
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Please fix the issues above.")
        return
    
    # Логируем начало основного процесса
    logger.info("Starting main processing loop")
    
    # Initialize lists to track failures
    failed_urls = []
    visual_analysis_failures = []
    processed_urls = []
    
    # Read URLs from links.txt
    try:
        with open('links.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(urls)} URLs from links.txt")
    except Exception as e:
        logger.error(f"Error reading links.txt: {str(e)}")
        logger.error(traceback.format_exc())
        return
    
    def normalize_url(url):
        # Remove trailing slash and index.html if present
        url = url.rstrip('/')
        if url.endswith('/index.html'):
            url = url[:-len('/index.html')]
        # Add project.json
        return f"{url}/project.json"

    # Process each URL through crawl module
    for index, url in enumerate(urls, 1):
        logger.info(f"Processing URL {index}/{len(urls)}: {url}")
        
        try:
            # Normalize URL to project.json format
            project_json_url = normalize_url(url)
            
            # First, crawl the project.json using the imported function
            logger.info(f"Attempting to crawl project.json at: {project_json_url}")
            result = crawl_url(project_json_url)
            
            if result:
                logger.info(f"Successfully processed URL with crawler: {url}")
                processed_urls.append(url)
                continue
            
            logger.warning(f"Failed to process with crawler, attempting JS extraction: {url}")
            
            # Try JSON extraction from JS files as fallback
            result = extract_js_json(url)
            if result:
                logger.info(f"Successfully processed URL using JS extraction: {url}")
                processed_urls.append(url)
                continue
                
            # If JS extraction fails, try traffic analysis
            logger.warning(f"JS extraction failed, attempting traffic analysis: {url}")
            analyzer = TrafficAnalyzer()
            try:
                result = analyzer.process_url(url)
                if result:
                    logger.info(f"Successfully processed URL using traffic analysis: {url}")
                    processed_urls.append(url)
                    continue
                else:
                    logger.error(f"All processing methods failed for URL: {url}")
                    failed_urls.append(url)
            finally:
                analyzer.close()
        except Exception as e:
            logger.error(f"Unhandled exception processing URL {url}: {str(e)}")
            logger.error(traceback.format_exc())
            failed_urls.append(url)
    
    # After crawling, run summarize.py
    logger.info("Running summarization process")
    success, output, error = run_script("summarize.py")
    if not success:
        logger.error(f"Summarization failed: {error}")
        return
    
    # Process screenshots and visual analysis
    for index, url in enumerate(processed_urls, 1):
        try:
            logger.info(f"Processing screenshots for URL {index}/{len(processed_urls)}: {url}")
            
            # Normalize URL and remove project.json for screenshot
            base_url = normalize_url(url).replace('/project.json', '/')
            
            # Get screenshot of the main page
            logger.info(f"Taking screenshot of: {base_url}")
            success, output, error = run_script("get_screenshoot_puppy.js", base_url)
            if not success:
                logger.error(f"Failed to get screenshot for: {base_url}")
                logger.error(f"Error: {error}")
                continue
                
            # Get screenshot name and path
            project_name = base_url.split('/')[-2]
            webp_path = f"screenshoots/{project_name}.webp"
            
            if not os.path.exists(webp_path):
                logger.error(f"Screenshot file not found at: {webp_path}")
                continue
                
            # Process the webp screenshot with vision_query
            logger.info(f"Analyzing visual style for: {webp_path}")
            
            # Запуск с улучшенной обработкой ошибок
            success, vision_output, vision_error = run_script("vision_query.py", webp_path)
            
            # Обработка результатов визуального анализа
            summary_path = f"summaries/{project_name}.md"
            
            if not success:
                logger.error(f"Vision query failed for: {webp_path}")
                logger.error(f"Error: {vision_error}")
                
                # Проверка на ошибку VPN
                if vision_output and "User location is not supported" in vision_output:
                    error_msg = "Error: VPN required for visual analysis."
                    logger.error(error_msg)
                    visual_analysis_failures.append(base_url)
                continue
                
            # Только запись действительных визуальных описаний
            if vision_output and not vision_output.startswith("Visual analysis error:"):
                logger.info(f"Adding visual description to: {summary_path}")
                try:
                    with open(summary_path, 'a') as f:
                        f.write(f"\n\nVisual: {vision_output.strip()}")
                    logger.info(f"Visual description added to {summary_path}")
                except Exception as e:
                    logger.error(f"Failed to update summary file: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
                
                # Обработка с process_md.py
                logger.info(f"Processing updated summary with process_md.py: {summary_path}")
                success, process_output, process_error = run_script("process_md.py", f"--update {summary_path} {base_url}")
                if not success:
                    logger.error(f"Failed to process {summary_path} with process_md.py")
                    logger.error(f"Error: {process_error}")
                else:
                    logger.info(f"Successfully processed {summary_path} with process_md.py")
        except Exception as e:
            logger.error(f"Unhandled exception in screenshot processing: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Финальное выполнение summarize.py
    logger.info("Running final summarization")
    success, output, error = run_script("summarize.py")
    if not success:
        logger.error(f"Final summarization failed: {error}")
    
    # Создание итогового отчета
    logger.info("Generating final report")
    timestamp = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
    
    report = [
        f"\n{timestamp} Processing summary:",
        f"  Total URLs processed: {len(urls)}",
        f"  Successfully processed: {len(processed_urls)}",
        f"  Failed to process: {len(failed_urls)}",
        f"  Visual analysis failures: {len(visual_analysis_failures)}"
    ]
    
    if failed_urls:
        report.append("  Failed URLs:")
        for url in failed_urls:
            report.append(f"    - {url}")
            
    if visual_analysis_failures:
        report.append("  Visual analysis failed URLs (VPN required):")
        for url in visual_analysis_failures:
            report.append(f"    - {url}")
    
    # Запись отчета в лог
    for line in report:
        logger.info(line)
    
    # Запись отчета в log.txt для обратной совместимости
    with open('log.txt', 'a') as log_file:
        for line in report:
            log_file.write(f"{line}\n")
    
    # Вывод отчета в консоль
    print("\n=== Processing Report ===")
    for line in report:
        print(line)
    
    logger.info("Process completed")

if __name__ == "__main__":
    # Инициализация логирования
    logger = setup_logging()
    
    try:
        main()
    except Exception as e:
        logger.critical("Unhandled exception in main process")
        logger.critical(str(e))
        logger.critical(traceback.format_exc())
        print("\nCRITICAL ERROR: Process failed. See logs for details.")
        sys.exit(1)