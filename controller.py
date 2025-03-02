#controller.py

import subprocess
import sys
import datetime
import os
import time
import logging
import traceback
import asyncio
import concurrent.futures
import random
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



# Асинхронная версия запуска скрипта с повторными попытками
async def run_script_async(script_name, args=None, max_retries=3, retry_delay=5):
    """
    Асинхронно запускает внешний скрипт с повторными попытками
    
    Args:
        script_name: Имя скрипта для запуска
        args: Строка аргументов для скрипта
        max_retries: Максимальное количество попыток
        retry_delay: Задержка между попытками в секундах
        
    Returns:
        tuple: (success, output, error)
    """
    # Использование ThreadPoolExecutor для запуска блокирующего кода в отдельном потоке
    attempt = 0
    last_error = ""
    
    while attempt < max_retries:
        attempt += 1
        
        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                success, output, error = await asyncio.get_event_loop().run_in_executor(
                    pool, run_script, script_name, args
                )
                
                if success:
                    if attempt > 1:
                        logger.info(f"Script {script_name} succeeded on attempt {attempt}")
                    return success, output, error
                
                last_error = error
                logger.warning(f"Script {script_name} failed (attempt {attempt}/{max_retries}): {error}")
                
                # Если это не последняя попытка, добавляем задержку перед следующей
                if attempt < max_retries:
                    # Добавляем небольшую случайность к задержке (±30%)
                    jitter = random.uniform(0.7, 1.3)
                    delay = retry_delay * jitter
                    logger.info(f"Retrying after {delay:.2f} seconds...")
                    await asyncio.sleep(delay)
        
        except Exception as e:
            last_error = str(e)
            logger.error(f"Exception running {script_name} (attempt {attempt}/{max_retries}): {last_error}")
            logger.error(traceback.format_exc())
            
            # Если это не последняя попытка, добавляем задержку перед следующей
            if attempt < max_retries:
                jitter = random.uniform(0.7, 1.3)
                delay = retry_delay * jitter
                logger.info(f"Retrying after {delay:.2f} seconds...")
                await asyncio.sleep(delay)
    
    # Если все попытки неудачны
    logger.error(f"Script {script_name} failed after {max_retries} attempts. Last error: {last_error}")
    return False, "", last_error

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

def normalize_url(url):
    # Remove trailing slash and index.html if present
    url = url.rstrip('/')
    if url.endswith('/index.html'):
        url = url[:-len('/index.html')]
    # Add project.json
    return f"{url}/project.json"

# Вспомогательная функция для обработки результатов визуального анализа
async def process_vision_and_update(webp_path, summary_path, base_url, max_retries=3):
    """
    Выполняет визуальный анализ и обновляет summary файл
    
    Args:
        webp_path: Путь к скриншоту
        summary_path: Путь к файлу summary
        base_url: Базовый URL
        max_retries: Максимальное количество попыток
        
    Returns:
        bool: Успешность операции
    """
    try:
        # Если summary файл не существует, пробуем запустить summarize.py для отдельного файла
        if not os.path.exists(summary_path):
            project_name = os.path.basename(summary_path).replace('.md', '')
            logger.warning(f"Summary file {summary_path} not found, trying to regenerate...")
            
            # Пытаемся найти исходный markdown файл
            md_file = f"markdown/{project_name}.md"
            if os.path.exists(md_file):
                logger.info(f"Found markdown file {md_file}, regenerating summary...")
                success, output, error = await run_script_async("summarize.py", f"{project_name}.md", max_retries=max_retries)
                if not success:
                    logger.error(f"Failed to regenerate summary for {project_name}: {error}")
                    return False
                
                if not os.path.exists(summary_path):
                    logger.error(f"Summary file still not found after regeneration attempt: {summary_path}")
                    return False
            else:
                logger.error(f"Original markdown file not found: {md_file}")
                return False
        
        # Запуск визуального анализа
        logger.info(f"Analyzing visual style for: {webp_path}")
        success, vision_output, vision_error = await run_script_async("vision_query.py", webp_path, max_retries=max_retries)
        
        if not success:
            logger.error(f"Vision query failed for: {webp_path}")
            logger.error(f"Error: {vision_error}")
            return False
        
        # Добавление визуального описания в файл сводки
        if vision_output and not vision_output.startswith("Visual analysis error:"):
            logger.info(f"Adding visual description to: {summary_path}")
            try:
                with open(summary_path, 'a') as f:
                    f.write(f"\n\nVisual: {vision_output.strip()}")
                logger.info(f"Visual description added to {summary_path}")
            except Exception as e:
                logger.error(f"Failed to update summary file: {str(e)}")
                logger.error(traceback.format_exc())
                return False
            
            # Обработка с vector_search.py
            logger.info(f"Processing updated summary with vector_search.py: {summary_path}")
            success, process_output, process_error = await run_script_async(
                "components/vector_search.py", 
                f"--update {summary_path} {base_url}",
                max_retries=max_retries
            )
            if not success:
                logger.error(f"Failed to process {summary_path} with vector_search.py")
                logger.error(f"Error: {process_error}")
                return False
            
            logger.info(f"Successfully processed {summary_path} with vector_search.py")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Unhandled exception in vision processing: {str(e)}")
        logger.error(traceback.format_exc())
        return False

async def main_async():
    # Настройки параллельности и повторных попыток
    MAX_CONCURRENT_SCREENSHOTS = 5  # Максимальное число параллельных скриншотов
    MAX_RETRIES = 3                 # Максимальное число повторных попыток
    
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
    screenshot_tasks = []
    
    # Семафор для ограничения параллельных скриншотов
    screenshot_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCREENSHOTS)
    
    # Read URLs from links.txt
    try:
        with open('links.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(urls)} URLs from links.txt")
    except Exception as e:
        logger.error(f"Error reading links.txt: {str(e)}")
        logger.error(traceback.format_exc())
        return
    
    # Асинхронная функция для создания скриншота с семафором
    async def create_screenshot(base_url):
        async with screenshot_semaphore:
            logger.info(f"Taking screenshot for: {base_url} (slots: {MAX_CONCURRENT_SCREENSHOTS - screenshot_semaphore._value}/{MAX_CONCURRENT_SCREENSHOTS})")
            return await run_script_async("get_screenshoot_puppy.js", base_url, max_retries=MAX_RETRIES)
    
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
                
                # Сразу запускаем создание скриншота, но не ждем завершения
                base_url = normalize_url(url).replace('/project.json', '/')
                logger.info(f"Starting screenshot task for: {base_url}")
                # Запускаем задачу через семафор для ограничения параллельности
                screenshot_task = asyncio.create_task(create_screenshot(base_url))
                screenshot_tasks.append((base_url, screenshot_task))
                
                continue
            
            logger.warning(f"Failed to process with crawler, attempting JS extraction: {url}")
            
            # Try JSON extraction from JS files as fallback
            result = extract_js_json(url)
            if result:
                logger.info(f"Successfully processed URL using JS extraction: {url}")
                processed_urls.append(url)
                
                # Сразу запускаем создание скриншота, но не ждем завершения
                base_url = normalize_url(url).replace('/project.json', '/')
                logger.info(f"Starting screenshot task for: {base_url}")
                # Запускаем задачу через семафор для ограничения параллельности
                screenshot_task = asyncio.create_task(create_screenshot(base_url))
                screenshot_tasks.append((base_url, screenshot_task))
                
                continue
                
            # If JS extraction fails, try traffic analysis
            logger.warning(f"JS extraction failed, attempting traffic analysis: {url}")
            analyzer = TrafficAnalyzer()
            try:
                result = analyzer.process_url(url)
                if result:
                    logger.info(f"Successfully processed URL using traffic analysis: {url}")
                    processed_urls.append(url)
                    
                    # Сразу запускаем создание скриншота, но не ждем завершения
                    base_url = normalize_url(url).replace('/project.json', '/')
                    logger.info(f"Starting screenshot task for: {base_url}")
                    # Запускаем задачу через семафор для ограничения параллельности
                    screenshot_task = asyncio.create_task(create_screenshot(base_url))
                    screenshot_tasks.append((base_url, screenshot_task))
                    
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
    
    # After crawling, run summarize.py (в этот момент скриншоты уже создаются параллельно)
    logger.info("Running summarization process")
    summarize_task = asyncio.create_task(run_script_async("summarize.py", max_retries=MAX_RETRIES))
    
    # Логируем, что задачи выполняются параллельно
    logger.info(f"Running {len(screenshot_tasks)} screenshot tasks and summarize.py in parallel")
    
    # Ждем завершения summarize.py
    success, output, error = await summarize_task
    
    if not success:
        logger.error(f"Summarization failed: {error}")
        # Продолжаем выполнение, чтобы дождаться завершения скриншотов
    else:
        logger.info("Summarization completed successfully")
    
    # Получаем список проектов, которые не удалось обработать в summarize.py
    summary_failures = []
    if output:
        # Ищем строки с "Failed to process X.md"
        for line in output.split('\n'):
            if "Failed to process" in line and ".md" in line:
                try:
                    failed_project = line.split("Failed to process ")[1].split(".md")[0]
                    summary_failures.append(failed_project)
                    logger.warning(f"Project {failed_project} failed in summarize.py")
                except:
                    pass
    
    # После завершения summarize.py, обрабатываем результаты скриншотов и добавляем визуальные описания
    vision_tasks = []
    retry_vision_tasks = []
    
    for base_url, screenshot_task in screenshot_tasks:
        try:
            project_name = base_url.split('/')[-2]
            summary_path = f"summaries/{project_name}.md"
            webp_path = f"screenshoots/{project_name}.webp"
            
            # Ждем завершения создания скриншота
            success, output, error = await screenshot_task
            
            if not success:
                logger.error(f"Screenshot failed for: {base_url}")
                logger.error(f"Error: {error}")
                visual_analysis_failures.append(base_url)
                continue
                
            if not os.path.exists(webp_path):
                logger.error(f"Screenshot file not found at: {webp_path}")
                visual_analysis_failures.append(base_url)
                continue
            
            # Проверяем, был ли проект в списке неудачных обработок summary
            if project_name in summary_failures:
                logger.warning(f"Project {project_name} had summary failure, adding to retry list")
                retry_vision_tasks.append((base_url, webp_path, summary_path))
                continue
                
            # Проверяем, существует ли summary-файл
            if not os.path.exists(summary_path):
                logger.warning(f"Summary file not found at: {summary_path}, adding to retry list")
                retry_vision_tasks.append((base_url, webp_path, summary_path))
                continue
            
            # Запускаем визуальный анализ и добавляем результат в список задач
            logger.info(f"Starting visual analysis for: {webp_path}")
            vision_task = asyncio.create_task(process_vision_and_update(webp_path, summary_path, base_url, max_retries=MAX_RETRIES))
            vision_tasks.append((base_url, vision_task))
            
        except Exception as e:
            logger.error(f"Error processing screenshot for {base_url}: {str(e)}")
            logger.error(traceback.format_exc())
            visual_analysis_failures.append(base_url)
    
    # Если есть задачи, которые нужно повторить из-за отсутствия summary файлов
    if retry_vision_tasks:
        logger.info(f"Attempting to retry {len(retry_vision_tasks)} vision tasks with missing summary files")
        
        for base_url, webp_path, summary_path in retry_vision_tasks:
            # Добавляем задержку перед повторной попыткой
            await asyncio.sleep(random.uniform(1, 3))
            
            try:
                logger.info(f"Retrying visual analysis for: {webp_path}")
                vision_task = asyncio.create_task(process_vision_and_update(webp_path, summary_path, base_url, max_retries=MAX_RETRIES))
                vision_tasks.append((base_url, vision_task))
            except Exception as e:
                logger.error(f"Error setting up retry for {base_url}: {str(e)}")
                visual_analysis_failures.append(base_url)
    
    # Ждем завершения всех задач визуального анализа
    for base_url, vision_task in vision_tasks:
        try:
            success = await vision_task
            if not success:
                visual_analysis_failures.append(base_url)
        except Exception as e:
            logger.error(f"Exception in vision task for {base_url}: {str(e)}")
            logger.error(traceback.format_exc())
            visual_analysis_failures.append(base_url)
    
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

def main():
    # Запуск асинхронного main
    asyncio.run(main_async())

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