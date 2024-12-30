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
    system_message = """YYou are an expert AI specializing in creating detailed, search-optimized game descriptions. Your task is to analyze games and create structured summaries that will be used by transformer models for semantic search.

Create a comprehensive description following this exact structure:

1. CORE IDENTIFICATION
Title: [game name] 
Author/Studio: [creator] 
Genre Tags: [list primary and secondary genres] 

2. GAMEPLAY FRAMEWORK
Core kinks:
- List 5-10 main gameplay kinks
- Describe how they interact
- Note any unique or innovative features

Player Agency:
- Type of choices available
- Impact of decisions
- Branching structure [linear/branching/open-ended]
- Replay value factors

3. NARRATIVE ELEMENTS
Plot Summary:
- 3-4 sentences capturing the main story 
- Include story setup and stakes

Key Characters:
- Protagonist description and role
- Major NPCs and their significance
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
- 2-3 comparable titles
- Reasons for similarity
- Key differences

Common Search Patterns:
- How players might remember this game
- Memorable scenes or moments
- Frequently referenced elements
- Common player descriptions

6. EXPERIENCE MARKERS
Emotional Impact:
- Key emotional moments 
- Memorable feelings
- Challenge level and type 
- Target audience appeal

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

Generated content should be both human-readable and optimized for AI processing."""
    
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
    
    # Call Poe API and collect response
    summary = ""
    async for partial in fp.get_bot_response(
        messages=messages,
        bot_name="4o-128k-free1",
        api_key=api_key
    ):
        summary += partial.text
        
    return summary

def save_summary(summary, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary)

import os
import shutil

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
