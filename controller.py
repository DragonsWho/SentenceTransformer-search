import subprocess
import sys
import datetime
import os
import time
from Components.traffic_analyzer import TrafficAnalyzer
from Components.js_json_extractor import extract_js_json

def run_script(script_name, args=None):
    try:
        # Use node for .js files, python for .py files
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
        
        # Capture and print output in real-time
        output_lines = []
        for line in process.stdout:
            print(line, end='')
            output_lines.append(line)
            
        # Capture and print stderr
        stderr_lines = []
        for line in process.stderr:
            print(f"ERROR: {line}", end='')
            stderr_lines.append(line)
            
        process.wait()
        
        # Check for JSON parsing errors in crawl.py output
        if script_name == "crawl.py" and any("Expecting value: line 1 column 1 (char 0)" in line for line in output_lines):
            return False
            
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, script_name)
            
        print(f"\n{script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running {script_name}: {e}")
        return False

def main():
    # Initialize lists to track failures
    failed_urls = []
    visual_analysis_failures = []
    
    # Read URLs from links.txt
    try:
        with open('links.txt', 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading links.txt: {e}")
        return
    
    def normalize_url(url):
        # Remove trailing slash and index.html if present
        url = url.rstrip('/')
        if url.endswith('/index.html'):
            url = url[:-len('/index.html')]
        # Add project.json
        return f"{url}/project.json"

    # Process each URL through crawl.py
    for url in urls:
        print(f"\nProcessing URL: {url}")
        
        # Normalize URL to project.json format
        project_json_url = normalize_url(url)
        
        # First, crawl the project.json
        if not run_script("crawl.py", project_json_url):
            print(f"Failed to process project.json, attempting traffic analysis for: {url}")
            
            # Try JSON extraction from JS files as fallback
            print(f"Attempting JSON extraction from JS files for: {url}")
            result = extract_js_json(url)
            if result:
                print(f"Successfully processed URL using JS JSON extraction: {url}")
                continue
                
            # If JS extraction fails, try traffic analysis
            print(f"JS JSON extraction failed, attempting traffic analysis for: {url}")
            analyzer = TrafficAnalyzer()
            try:
                result = analyzer.process_url(url)
                if result:
                    print(f"Successfully processed URL using traffic analysis: {url}")
                    continue
                else:
                    print(f"Traffic analysis failed for: {url}")
                    failed_urls.append(url)
                    continue
            finally:
                analyzer.close()
    
    # After crawling, run summarize.py
    if not run_script("summarize.py"):
        print("Summarization failed")
        return
    
    # Then process screenshots and visual analysis
    for url in urls:
        # Normalize URL and remove project.json for screenshot
        base_url = normalize_url(url).replace('/project.json', '/')
        print(f"\nProcessing screenshots for: {base_url}")
        
        # Get screenshot of the main page
        if not run_script("get_screenshoot_puppy.js", base_url):
            print(f"Failed to get screenshot for: {base_url}")
            continue
            
        # Get screenshot name and path
        project_name = base_url.split('/')[-2]
        webp_path = f"screenshoots/{project_name}.webp"
        
        # Process the webp screenshot with vision_query
        print(f"Analyzing visual style for: {webp_path}")
        
        # Run vision_query and capture output
        process = subprocess.Popen(
            [sys.executable, "vision_query.py", webp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        # Append visual description to summary file
        summary_path = f"summaries/{project_name}.md"
        try:
            # Handle errors first
            print(f"DEBUG: vision_query output: {stdout.strip()}")
            
            if not stdout.strip():
                print("No visual description available")
                return
                
            # Check for VPN-related error in the raw message
            if "User location is not supported" in stdout.strip():
                error_msg = "Error: VPN required for visual analysis. Please enable VPN and try again."
                print(error_msg)
                with open("log.txt", 'a') as log_file:
                    log_file.write(f"\n{datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]')} {error_msg}")
                visual_analysis_failures.append(base_url)
                print("DEBUG: Added VPN failure to tracking list")
                return
                
            # Only write valid visual descriptions
            if not stdout.strip().startswith("Visual analysis error:"):
                with open(summary_path, 'a') as f:
                    f.write(f"\n\nVisual: {stdout.strip()}")
                print(f"Visual description added to {summary_path}")
        except Exception as e:
            print(f"Failed to update summary file: {e}")
            
            # Process the new summary with process_md.py
            print(f"\nCalling process_md.py with: --update {summary_path} {base_url}")
            if not run_script("process_md.py", f"--update {summary_path} {base_url}"):
                print(f"Failed to process {summary_path} with process_md.py")
            else:
                print(f"Successfully processed {summary_path} with process_md.py")
        except Exception as e:
            print(f"Failed to update summary file: {e}")
            continue
    if not run_script("summarize.py"):
        print("Summarization failed")
        return
    
    # Append processing summary to log.txt
    timestamp = datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]')
    with open('log.txt', 'a') as log_file:
        log_file.write(f"\n{timestamp} Processing summary:\n")
        log_file.write(f"  Total URLs processed: {len(urls)}\n")
        log_file.write(f"  Successfully processed: {len(urls) - len(failed_urls)}\n")
        log_file.write(f"  Failed to process: {len(failed_urls)}\n")
        
        if failed_urls:
            log_file.write("  Failed URLs:\n")
            for url in failed_urls:
                log_file.write(f"    - {url}\n")

    # Print summary
    print("\n=== Processing Report ===")
    print(f"Total URLs processed: {len(urls)}")
    print(f"Successfully processed: {len(urls) - len(failed_urls)}")
    print(f"Failed to process: {len(failed_urls)}")
    print(f"Visual analysis failures: {len(visual_analysis_failures)}")
    
    if failed_urls:
        print("\nFailed URLs:")
        for i, url in enumerate(failed_urls, 1):
            print(f"{i}. {url}")
            
    if visual_analysis_failures:
        print("\nVisual analysis failed URLs (VPN required):")
        for i, url in enumerate(visual_analysis_failures, 1):
            print(f"{i}. {url}")
    
    print("\nSummarization completed")
    if visual_analysis_failures:
        print("Note: Some visual analyses failed due to VPN requirements. Please enable VPN and retry.")

if __name__ == "__main__":
    main()
