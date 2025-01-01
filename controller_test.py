import subprocess
import sys
import os

def run_script(script_name, args=None):
    try:
        command = [sys.executable, script_name]
        if args:
            command.extend(args.split())
            
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Capture and print output in real-time
        for line in process.stdout:
            print(line, end='')
            
        process.wait()
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, script_name)
            
        print(f"\n{script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError running {script_name}: {e}")
        return False

def main():
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
        
        # Crawl the project.json
        if not run_script("crawl.py", project_json_url):
            print(f"Failed to process URL: {project_json_url}")
            continue

if __name__ == "__main__":
    main()
