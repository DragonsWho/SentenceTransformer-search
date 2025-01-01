import subprocess
import sys

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
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Print output in real-time
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
    
    # Process each URL through crawl.py
    for url in urls:
        print(f"\nProcessing URL: {url}")
        
        # First, crawl the project.json
        if not run_script("crawl.py", url):
            print(f"Failed to process URL: {url}")
            continue
    
    # After crawling, run summarize.py
    if not run_script("summarize.py"):
        print("Summarization failed")
        return
    
    # Then process screenshots and visual analysis
    for url in urls:
        base_url = url.replace('/project.json', '/')
        print(f"\nProcessing screenshots for: {base_url}")
        
        # Get screenshot of the main page
        if not run_script("get_screenshoot_puppy.js", base_url):
            print(f"Failed to get screenshot for: {base_url}")
            continue
            
        # Process the webp screenshot with vision_query
        project_name = base_url.split('/')[-2]
        webp_path = f"screenshoots/{project_name}.webp"
        print(f"Analyzing visual style for: {webp_path}")
        if not run_script("vision_query.py", webp_path):
            print(f"Failed to analyze visual style for: {webp_path}")
            continue
    if not run_script("summarize.py"):
        print("Summarization failed")
        return
    
    print("All URLs processed and summarization completed")

if __name__ == "__main__":
    main()
