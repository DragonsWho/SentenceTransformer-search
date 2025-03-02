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

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(f"logs/process_{date_str}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("Process started")
    
    return logging.getLogger()

def run_script(script_name, args=None):
    """
    Runs an external script with advanced logging and checks
    
    Args:
        script_name: The name of the script to run
        Args: Argument string for the script
        
    Returns:
        tuple: (success, output, error)
    """
    if not os.path.exists(script_name):
        logger.error(f"Script file not found: {script_name}")
        return False, "", f"File not found: {script_name}"
    
    try:
        if script_name.endswith('.js'):
            command = ['node', script_name]
        else:
            command = [sys.executable, script_name]
            
        if args:
            command.extend(args.split())
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        output_lines = []
        error_lines = []
        
        def process_output(stream, prefix, output_list):
            for line in stream:
                line = line.strip()
                if line:
                    output_list.append(line)
        
        process_output(process.stdout, "OUTPUT", output_lines)
        process_output(process.stderr, "ERROR", error_lines)
        
        process.wait()
        
        output = "\n".join(output_lines)
        error = "\n".join(error_lines)
        
        if process.returncode != 0:
            logger.error(f"Script returned non-zero exit code: {process.returncode}")
            return False, output, error
            
        return True, output, error
    
    except subprocess.TimeoutExpired:
        return False, "", "Timeout expired"
    except Exception as e:
        logger.error(f"Error running script: {script_name}")
        return False, "", str(e)

async def run_script_async(script_name, args=None, max_retries=3, retry_delay=5):
    """
    Asynchronously runs an external script with retries
    
    Args:
        script_name: The name of the script to run
        args: Argument string for the script
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        
    Returns:
        tuple: (success, output, error)
    """
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
                    return success, output, error
                
                last_error = error
                
                if attempt < max_retries:
                    jitter = random.uniform(0.7, 1.3)
                    delay = retry_delay * jitter
                    await asyncio.sleep(delay)
        
        except Exception as e:
            last_error = str(e)
            
            if attempt < max_retries:
                jitter = random.uniform(0.7, 1.3)
                delay = retry_delay * jitter
                await asyncio.sleep(delay)
    
    logger.error(f"Script {script_name} failed after {max_retries} attempts. Last error: {last_error}")
    return False, "", last_error

def check_prerequisites():
    """Проверка необходимых условий перед запуском"""
    prerequisites_met = True
    
    for directory in ["markdown", "summaries", "screenshoots"]:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    if not os.path.exists("links.txt"):
        logger.error("links.txt file not found!")
        prerequisites_met = False
    else:
        with open("links.txt", "r") as f:
            urls = [line.strip() for line in f if line.strip()]
            if not urls:
                logger.error("links.txt file is empty!")
                prerequisites_met = False
    
    try:
        result = subprocess.run(["node", "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        if result.returncode != 0:
            logger.error("Node.js not found! Required for JavaScript scripts.")
            prerequisites_met = False
    except:
        logger.error("Error checking Node.js. Make sure it's installed.")
        prerequisites_met = False
    
    return prerequisites_met

def normalize_url(url):
    url = url.rstrip('/')
    if url.endswith('/index.html'):
        url = url[:-len('/index.html')]
    return f"{url}/project.json"

async def process_vision_and_update(webp_path, summary_path, base_url, max_retries=3):
    """
    Performs visual analysis and updates summary file
    
    Args:
        webp_path: Path to screenshot
        summary_path: Path to summary file
        base_url: Base URL
        max_retries: Maximum number of attempts
        
    Returns:
        bool: Successful operation
    """
    try:
        if not os.path.exists(summary_path):
            project_name = os.path.basename(summary_path).replace('.md', '')
            
            md_file = f"markdown/{project_name}.md"
            if os.path.exists(md_file):
                success, output, error = await run_script_async("summarize.py", f"{project_name}.md", max_retries=max_retries)
                if not success:
                    return False
                
                if not os.path.exists(summary_path):
                    return False
            else:
                return False
        
        success, vision_output, vision_error = await run_script_async("vision_query.py", webp_path, max_retries=max_retries)
        
        if not success:
            return False
        
        if vision_output and not vision_output.startswith("Visual analysis error:"):
            try:
                with open(summary_path, 'a') as f:
                    f.write(f"\n\nVisual: {vision_output.strip()}")
            except Exception:
                return False
            
            success, process_output, process_error = await run_script_async(
                "components/vector_search.py", 
                f"--update {summary_path} {base_url}",
                max_retries=max_retries
            )
            if not success:
                return False
            
            return True
        
        return False
    except Exception:
        return False

async def main_async():
    MAX_CONCURRENT_SCREENSHOTS = 5
    MAX_RETRIES = 3
    
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Please fix the issues above.")
        return
    
    logger.info("Starting main processing loop")
    
    failed_urls = []
    visual_analysis_failures = []
    processed_urls = []
    screenshot_tasks = []
    
    screenshot_semaphore = asyncio.Semaphore(MAX_CONCURRENT_SCREENSHOTS)
    
    try:
        with open('links.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(urls)} URLs from links.txt")
    except Exception as e:
        logger.error(f"Error reading links.txt: {str(e)}")
        return
    
    async def create_screenshot(base_url):
        async with screenshot_semaphore:
            return await run_script_async("get_screenshoot_puppy.js", base_url, max_retries=MAX_RETRIES)
    
    for index, url in enumerate(urls, 1):
        logger.info(f"Processing URL {index}/{len(urls)}: {url}")
        
        try:
            project_json_url = normalize_url(url)
            
            result = crawl_url(project_json_url)
            
            if result:
                processed_urls.append(url)
                
                base_url = normalize_url(url).replace('/project.json', '/')
                screenshot_task = asyncio.create_task(create_screenshot(base_url))
                screenshot_tasks.append((base_url, screenshot_task))
                
                continue
            
            result = extract_js_json(url)
            if result:
                processed_urls.append(url)
                
                base_url = normalize_url(url).replace('/project.json', '/')
                screenshot_task = asyncio.create_task(create_screenshot(base_url))
                screenshot_tasks.append((base_url, screenshot_task))
                
                continue
                
            analyzer = TrafficAnalyzer()
            try:
                result = analyzer.process_url(url)
                if result:
                    processed_urls.append(url)
                    
                    base_url = normalize_url(url).replace('/project.json', '/')
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
            failed_urls.append(url)
    
    logger.info("Running summarization process")
    summarize_task = asyncio.create_task(run_script_async("summarize.py", max_retries=MAX_RETRIES))
    
    success, output, error = await summarize_task
    
    if not success:
        logger.error(f"Summarization failed: {error}")
    
    summary_failures = []
    if output:
        for line in output.split('\n'):
            if "Failed to process" in line and ".md" in line:
                try:
                    failed_project = line.split("Failed to process ")[1].split(".md")[0]
                    summary_failures.append(failed_project)
                except:
                    pass
    
    vision_tasks = []
    retry_vision_tasks = []
    
    for base_url, screenshot_task in screenshot_tasks:
        try:
            project_name = base_url.split('/')[-2]
            summary_path = f"summaries/{project_name}.md"
            webp_path = f"screenshoots/{project_name}.webp"
            
            success, output, error = await screenshot_task
            
            if not success:
                visual_analysis_failures.append(base_url)
                continue
                
            if not os.path.exists(webp_path):
                visual_analysis_failures.append(base_url)
                continue
            
            if project_name in summary_failures:
                retry_vision_tasks.append((base_url, webp_path, summary_path))
                continue
                
            if not os.path.exists(summary_path):
                retry_vision_tasks.append((base_url, webp_path, summary_path))
                continue
            
            vision_task = asyncio.create_task(process_vision_and_update(webp_path, summary_path, base_url, max_retries=MAX_RETRIES))
            vision_tasks.append((base_url, vision_task))
            
        except Exception:
            visual_analysis_failures.append(base_url)
    
    if retry_vision_tasks:
        for base_url, webp_path, summary_path in retry_vision_tasks:
            await asyncio.sleep(random.uniform(1, 3))
            
            try:
                vision_task = asyncio.create_task(process_vision_and_update(webp_path, summary_path, base_url, max_retries=MAX_RETRIES))
                vision_tasks.append((base_url, vision_task))
            except Exception:
                visual_analysis_failures.append(base_url)
    
    for base_url, vision_task in vision_tasks:
        try:
            success = await vision_task
            if not success:
                visual_analysis_failures.append(base_url)
        except Exception:
            visual_analysis_failures.append(base_url)
    
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
    
    for line in report:
        logger.info(line)
    
    with open('log.txt', 'a') as log_file:
        for line in report:
            log_file.write(f"{line}\n")
    
    print("\n=== Processing Report ===")
    for line in report:
        print(line)
    
    logger.info("Process completed")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    logger = setup_logging()
    
    try:
        main()
    except Exception as e:
        logger.critical("Unhandled exception in main process")
        logger.critical(str(e))
        logger.critical(traceback.format_exc())
        print("\nCRITICAL ERROR: Process failed. See logs for details.")
        sys.exit(1)