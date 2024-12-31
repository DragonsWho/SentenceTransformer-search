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
    system_message = """You are an expert AI specializing in creating detailed, search-optimized game descriptions. Your task is to analyze games and create structured summaries that will be used by transformer models for semantic search. Generated content should be both human-readable and optimized for AI processing.

Take into account that the search will be performed using free-form user queries. Try to use search words that most accurately describe the game, its most memorable features. 

Don't write anything but summarize in the message, the response will be handled by the script and put entirely into the database. All the games in the base are CYOA, no need to mention this feature.

you can and should use the RIGHT names for kinks and features, even if they are dirty, lewd words. Accuracy of search is paramount. 

Create a comprehensive description following this exact structure:

 
Title: [game name] (Add 10 queries with typical errors to increase the probability of search success)
Author: [creator] 
Genre Tags: [list primary and secondary genres] 7-12 pieces

 
Core kinks:
- List 10-15 main gameplay kinks. Add synonyms to improve search 
- Note any unique or innovative features
 

 
Plot Summary:
- 7-10 sentences capturing the main story 
- Include story setup and stakes  

Write list the main sections

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
- what popular settings it feels like (only if the game explicitly uses references to popular setting or parodies them)

4. DISTINCTIVE FEATURES
Unique Selling Points:
- What makes this game special
- Innovative elements 

Themes and Tone:
- Main themes explored
- Emotional atmosphere
- Writing style
- Narrative approach

 

Common Search Patterns: (dont use word "CYOA")
Common Search Patterns:
Write 12-15 different ways how users might try to find this game, including:

1. Memory-based queries (4-5 examples):
- "I remember game where [memorable scene/situation]"
- "looking for game with [distinct character/feature]"
- "there was this scene where [specific event]"
- Include common mistakes in names/terms

2. Emotional/Subjective searches (3-4 examples):
- "[emotional reaction] story about [theme]"
- "game that made me feel [emotion] when [event]"
- Use casual/colloquial language

3. Feature-focused searches (3-4 examples):
- "game where you can [unique mechanic/possibility]"
- "story about [main theme] with [distinct element]"
- Include alternative terms for key features

4. Scene/Situation searches (2-3 examples):
- "that game where [specific situation happens]"
- Include most memorable or unique moments

For each search pattern:
- Use natural, conversational language
- Include common alternative terms
- Mix specific and vague descriptions
- Add realistic misspellings where appropriate
- Include emotional reactions and subjective impressions
- Use both formal and slang terms for adult content
- Consider how different players might remember same elements

Important: Write these as real search queries, not descriptions. Make them sound like actual forum posts or search requests.
 
 

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
