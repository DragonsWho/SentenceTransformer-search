from deepseek_api import call_deepseek_chat
import json

import time

def summarize_md_file(file_path):
    # Check file size (max 100KB)
    file_size = os.path.getsize(file_path)
    if file_size > 100 * 1024:  # 100KB
        print(f"File {os.path.basename(file_path)} is too large ({file_size} bytes). Skipping.")
        return None
        
    # Read the markdown file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Add delay between API calls
    time.sleep(2)
    
    # Create system message
    system_message = """You are an expert in summarizing complex game narratives. 
    Create a concise summary in Markdown format that captures the key elements of the game's story, 
    mechanics, and world-building. The summary will be used for transformer-based 
    search and analysis, so it should be:
    1. Informative but concise
    2. Include key characters, mechanics, and world details
    3. Maintain the original tone and style
    4. Use proper Markdown formatting (headers, lists, etc.)
    5. Be structured for easy parsing by AI systems"""
    
    # Create user message
    user_message = f"""Here is the content of the game file. Please create a summary 
    following the guidelines above:\n\n{content}"""
    
    # Call the API
    result = call_deepseek_chat(system_message, user_message)
    
    # Extract and clean the summary
    if 'choices' in result and len(result['choices']) > 0:
        summary = result['choices'][0]['message']['content']
        # Replace escaped newlines with actual newlines
        summary = summary.replace('\\n', '\n')
        return summary
    return None

def save_summary(summary, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary)

import os
import shutil

def process_all_md_files():
    # Ensure directories exist
    os.makedirs("summaries", exist_ok=True)
    os.makedirs("markdown/archive", exist_ok=True)
    
    # Get all .md files in markdown directory
    md_files = [f for f in os.listdir("markdown") if f.endswith(".md")]
    
    for md_file in md_files:
        input_path = os.path.join("markdown", md_file)
        output_path = os.path.join("summaries", f"{os.path.splitext(md_file)[0]}_summary.md")
        
        print(f"Processing {md_file}...")
        summary = summarize_md_file(input_path)
        
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
    process_all_md_files()
