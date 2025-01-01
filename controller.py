import subprocess
import sys

def run_script(script_name):
    try:
        result = subprocess.run([sys.executable, script_name], check=True)
        print(f"{script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    # Run crawl.py first
    if not run_script("crawl.py"):
        print("Crawling failed, aborting process")
        return
    
    # If crawl succeeded, run summarize.py
    if not run_script("summarize.py"):
        print("Summarization failed")
        return
    
    print("Both scripts completed successfully")

if __name__ == "__main__":
    main()
