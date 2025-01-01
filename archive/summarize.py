import fastapi_poe as fp
import json
import time
import os
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    # Create system message
    system_message = """You are an expert AI specializing in creating detailed, search-optimized game descriptions. Your task is to analyze games and create structured summaries that will be used by transformer models for semantic search. Generated content should be both human-readable and optimized for AI processing.

Take into account that the search will be performed using free-form user queries. Try to use search words that most accurately describe the game, its most memorable features. 

Don't write anything but summarize in the message, the response will be handled by the script and put entirely into the database. All the games in the base are CYOA, no need to mention this feature.

you can and should use the RIGHT names for kinks and features, even if they are dirty, lewd words. Accuracy of search is paramount. 

Create a comprehensive description following this exact structure:

1. CORE IDENTIFICATION
Title: [game name] 
Author: [creator] 
Genre Tags: [list primary and secondary genres] 

2. GAMEPLAY FRAMEWORK
Core kinks:
- List 10-20 main gameplay kinks 
- Note any unique or innovative features
 

3. NARRATIVE ELEMENTS
Plot Summary:
- 4-5 sentences capturing the main story 
- Include story setup and stakes 
- most memorable moments

Key Characters:
- Protagonist description and role
- other Key Characters and their significance
- Antagonist(s) if present
- Important relationships

Setting Details:
- Time period and world type
- Major locations
- World-building elements
- Atmospheric description
- what popular settings it feels like

4. DISTINCTIVE FEATURES
Unique Selling Points:
- What makes this game special
- Innovative elements
- Memorable moments 

Themes and Tone:
- Main themes explored
- Emotional atmosphere
- Writing style
- Narrative approach

5. CONTEXTUAL INFORMATION
Similar Games:
- 10-15 comparable titles without descriptions 

Common Search Patterns: (15 examples)
- How players might remember this game
- Memorable scenes or moments
- Frequently referenced elements
- Common player descriptions

6. EXPERIENCE MARKERS
Emotional Impact:
- Key emotional moments 
- Memorable feelings
 

FORMAT REQUIREMENTS:
- Use clear, concise language
- Include specific proper nouns and unique identifiers
- Maintain consistent structure
- Use standard YAML/Markdown formatting
- Prioritize searchable elements and keywords
- Include alternative terms for key concepts
- Avoid technical jargon unless genre-specific
- Balance detail with brevity

IMPORTANT CONSIDERATIONS:
1. Focus on elements players are likely to remember
2. Include both objective facts and subjective experiences
3. Maintain searchable terminology while preserving unique elements
4. Consider how different players might describe or remember the game
5. Include context that helps distinguish from similar games
6. Preserve tone and style markers that make the game unique

Your summary should function effectively for:
- Natural language queries
- Semantic similarity matching
- Feature-based searching
- Memory-based player queries
- Recommendation systems
- Context-aware analysis
"""
    
    # Create user message
    user_message = f"""Here is the content of the game file. Please create a summary 
    following the guidelines above:\n\n{content}"""
    
    # Create messages for Poe API
    messages = [
        fp.ProtocolMessage(role="system", content=system_message),
        fp.ProtocolMessage(role="user", content=user_message)
    ]
    
    # Get API key from environment
    api_key = os.getenv('POE_API_KEY')
    
    # Call Poe API with enhanced error handling
    max_retries = 5
    retry_delay = 10  # seconds
    bots_to_try = [
        "4o-128k-free1"
    ]
    
    # Log API status
    api_status_file = "api_status.log"
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
    for attempt in range(max_retries):
        for bot_name in bots_to_try:
            try:
                summary = ""
                async for partial in fp.get_bot_response(
                    messages=messages,
                    bot_name=bot_name,
                    api_key=api_key
                ):
                    summary += partial.text
                
                # Log successful API call
                with open(api_status_file, "a") as log:
                    log.write(f"{current_time} - Success using {bot_name}\n")
                return summary
                
            except fp.BotError as e:
                error_msg = f"{current_time} - Error in Poe bot {bot_name} (attempt {attempt + 1}): {str(e)}\n"
                print(error_msg)
                with open(api_status_file, "a") as log:
                    log.write(error_msg)
                    
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                
                # After final attempt, notify and pause
                print("\nPoe API is currently unavailable. Pausing summarization process.")
                print("Will automatically retry in 1 hour. Check api_status.log for details.")
                time.sleep(3600)  # Wait 1 hour before retrying
                return None
                
            except Exception as e:
                error_msg = f"{current_time} - Unexpected error with bot {bot_name}: {str(e)}\n"
                print(error_msg)
                with open(api_status_file, "a") as log:
                    log.write(error_msg)
                    
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise
                
    return None

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
