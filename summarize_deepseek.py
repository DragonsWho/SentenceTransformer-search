import os
import time
import shutil
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def call_deepseek_chat(system_message: str, user_message: str) -> str:
    """
    Calls Deepseek API to get a summary response
    
    Args:
        system_message (str): System message defining the assistant's behavior
        user_message (str): User message with content to summarize
        
    Returns:
        str: Generated summary text
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Deepseek API error: {str(e)}")
        return None

async def summarize_md_file(file_path):
    # Check file size (max 1100KB)
    file_size = os.path.getsize(file_path)
    if file_size > 1100 * 1024:  # 1100KB
        print(f"File {os.path.basename(file_path)} is too large ({file_size} bytes). Skipping.")
        return None
        
    # Read the markdown file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Add delay between API calls
    time.sleep(2)
    
    # Create system message (same as in summarize.py)
    system_message = """You are an expert AI specializing in creating detailed, search-optimized game descriptions..."""  # [Full system message from summarize.py]
    
    # Create user message
    user_message = f"""Here is the content of the game file. Please create a summary 
    following the guidelines above:\n\n{content}"""
    
    # Call Deepseek API
    return call_deepseek_chat(system_message, user_message)

def save_summary(summary, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary)

async def process_all_md_files():
    # Ensure directories exist
    os.makedirs("summaries", exist_ok=True)
    os.makedirs("markdown/archive", exist_ok=True)
    
    # Get all .md files in markdown directory
    md_files = [f for f in os.listdir("markdown") if f.endswith(".md")]
    
    for md_file in md_files:
        input_path = os.path.join("markdown", md_file)
        output_path = os.path.join("summaries", f"{os.path.splitext(md_file)[0]}_summary.md")
        
        print(f"Processing {md_file}...")
        summary = await summarize_md_file(input_path)
        
        if summary:
            save_summary(summary, output_path)
            print(f"Summary saved to {output_path}")
            
            # Move processed file to archive
            archive_path = os.path.join("markdown/archive", md_file)
            shutil.move(input_path, archive_path)
            print(f"Moved {md_file} to archive")
        else:
            print(f"Failed to process {md_file}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(process_all_md_files())
