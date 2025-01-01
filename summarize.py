import os
import time
import shutil
from dotenv import load_dotenv
import requests
import tiktoken
from detect_repetition import detect_repetition

# Load environment variables
load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
CHUNK_SIZE = 60000  # Approximate token count per chunk

def call_deepseek_chat(system_message: str, user_message: str) -> str:
    """Calls Deepseek API to get a summary response"""
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
        content = response.json()['choices'][0]['message']['content']
        
        # Check for repetition in LLM response
        if detect_repetition(content, sequence_length=3, min_repeats=10):
            print("Warning: Detected repetition in LLM response. Retrying with modified prompt...")
            payload['messages'][0]['content'] += "\nAvoid repeating phrases or sentences. Provide concise, varied responses."
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            
        return content
    except Exception as e:
        print(f"Deepseek API error: {str(e)}")
        return None

def split_into_chunks(text, chunk_size):
    """Split text into chunks using precise token counting"""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoding.encode(text)
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = start + chunk_size
        if end > len(tokens):
            end = len(tokens)
        
        chunk_text = encoding.decode(tokens[start:end])
        chunks.append(chunk_text)
        start = end
    
    return chunks

async def summarize_chunk(chunk, system_message):
    """Summarize a single chunk of text"""
    time.sleep(2)  # Rate limiting
    return call_deepseek_chat(system_message, chunk)

async def summarize_md_file(file_path):
    """Process single Markdown file with chunking"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    chunks = split_into_chunks(content, CHUNK_SIZE)
    if not chunks:
        return None
          
    
    
    # System messages
    first_chunk_system_message =  """ANALYZE THIS NSFW CYOA TEXT CHUNK:
Create a detailed intermediate summary focusing on NEW and UNIQUE elements. Use casual language and include alternative terms. This data will be used for final game summarization and semantic search so include details that players might search for later.

List these elements if present in the chunk:

0.This is the very first chunk, the beginning of the game. Try to find the name of the game and the author's name and write them especially clearly at the beginning of the report.  Highlight them. 
1. Title: [exact game title]
2. Author: [creator name]

Story:
- Plot events 
- Chapter descriptions
- Core characters and relationships
- Setting details
- Memorable scenes
- Story branches

Gameplay:
- New features and mechanics
- Powers and abilities
- Character options
- Progress systems

Adult Content:
- Kinks and fetishes
- Sexual systems and mechanics
- Romance/relationship options
- Body modifications/transformations
- Training/corruption elements
- Unique adult scenes

Distinctive Features:
- Memorable moments and dialogue
- Unique combinations
- Special abilities
- Rare or creative elements
- Phrases players might search for

Keep descriptions specific but brief - this is intermediate data for further processing."""



 
    chunk_system_message = """ANALYZE THIS NSFW CYOA TEXT CHUNK:
Create a detailed intermediate summary focusing on NEW and UNIQUE elements. Use casual language and include alternative terms. This data will be used for final game summarization and semantic search so include details that players might search for later.

List these elements if present in the chunk:

Story:
- Plot events 
- Chapter descriptions
- Core characters and relationships
- Setting details
- Memorable scenes
- Story branches

Gameplay:
- New features and mechanics
- Powers and abilities
- Character options
- Progress systems

Adult Content:
- Kinks and fetishes
- Sexual systems and mechanics
- Romance/relationship options
- Body modifications/transformations
- Training/corruption elements
- Unique adult scenes

Distinctive Features:
- Memorable moments and dialogue
- Unique combinations
- Special abilities
- Rare or creative elements
- Phrases players might search for

Keep descriptions specific but brief - this is intermediate data for further processing."""







    combine_system_message = """  
You are an expert AI specializing in creating detailed, search-optimized game descriptions. Your task is to combine multiple partial summaries into a comprehensive, search-optimized game descriptions for transformer-based semantic searc.

1. Combine information from all partial summaries
2. Remove any duplicate information
3. Create a coherent narrative flow
4. Maintain all important details
5. Structure the final summary according to the standard format:
 
All games are CYOA - omit mentioning this. Use accurate terminology for kinks and features, including explicit terms when needed. Keep descriptions concise but informative. Skip formatting and bullet points.

Structure:

Title: [game name] ([10 common misspellings/typing errors in brackets]:
- Missing letter
- Double letter
- Swapped letters
- No spaces
- Wrong similar-sounding letter
- Keyboard adjacent error
- Autocorrect error
- Phonetic misspelling
- Split word)

Author: [creator]
Genre Tags: [7-12 primary/secondary genres]

Kinks: [10 main gameplay kinks with synonyms, unique features]

Plot: [7-10 sentences covering setup, stakes, main story]

Setting:
- Core location/world details
- Atmosphere
- Similar popular settings (only if explicitly referenced)

Themes:
- Main themes
- Emotional tone
- Atmosphere

Characters: [brief description of protagonist and key characters that drive the story]

Search Patterns: [7 natural user queries]
Write as forum posts/searches like:
"I remember game where [scene]"
"looking for game with [feature]"
"there was this scene where [event]"
"[emotion] story about [theme]"

Focus on:
- Memorable elements
- Natural language
- Alternative terms
- Common misspellings
- Both specific details and vague memories
- Formal and informal terminology
- Different player perspectives

Prioritize searchable elements while preserving unique game characteristics.
 
    
"""














    full_game_system_message = """You are an expert AI creating detailed, search-optimized game descriptions for transformer-based semantic search. Generate content that is both human-readable and AI-optimized.

All games are CYOA - omit mentioning this. Use accurate terminology for kinks and features, including explicit terms when needed. Keep descriptions concise but informative. Skip formatting and bullet points.

Structure:

Title: [game name] ([10 common misspellings/typing errors in brackets]:
- Missing letter
- Double letter
- Swapped letters
- No spaces
- Wrong similar-sounding letter
- Keyboard adjacent error
- Autocorrect error
- Phonetic misspelling
- Split word)

Author: [creator]
Genre Tags: [7-12 primary/secondary genres]

Kinks: [10 main gameplay kinks with synonyms, unique features]

Plot: [7-10 sentences covering setup, stakes, main story]

Setting:
- Core location/world details
- Atmosphere
- Similar popular settings (only if explicitly referenced)

Themes:
- Main themes
- Emotional tone
- Atmosphere

Characters: [brief description of protagonist and key characters that drive the story]

Search Patterns: [7 natural user queries]
Write as forum posts/searches like:
"I remember game where [scene]"
"looking for game with [feature]"
"there was this scene where [event]"
"[emotion] story about [theme]"

Focus on:
- Memorable elements
- Natural language
- Alternative terms
- Common misspellings
- Both specific details and vague memories
- Formal and informal terminology
- Different player perspectives

Prioritize searchable elements while preserving unique game characteristics.
"""
     








    # If single chunk, use full summary prompt
    if len(chunks) == 1:
        return await summarize_chunk(chunks[0], full_game_system_message)
        
    # Process first chunk separately and save it
    title_author = await summarize_chunk(chunks[0], first_chunk_system_message)
    
    # Save first chunk with metadata
    os.makedirs("markdown/archive_chanks", exist_ok=True)
    chunk_path = os.path.join("markdown/archive_chanks", 
                            f"{os.path.splitext(os.path.basename(file_path))[0]}_chunk0.md")
    
    with open(chunk_path, 'w', encoding='utf-8') as f:
        f.write(f"=== ORIGINAL CHUNK ===\n{chunks[0]}\n\n")
        f.write(f"=== METADATA ===\n{title_author}\n")
        
    print(f"Saved first chunk analysis to {chunk_path}")
    
    # Process remaining chunks
    chunk_summaries = []
    for i, chunk in enumerate(chunks[1:], start=1):
        print(f"Processing chunk {i+1}/{len(chunks)} of {os.path.basename(file_path)}")
        summary = await summarize_chunk(chunk, chunk_system_message)
        if summary:
            chunk_summaries.append(summary)
            
            # Save intermediate chunk summary with detailed logging
            os.makedirs("markdown/archive_chanks", exist_ok=True)
            chunk_path = os.path.join("markdown/archive_chanks", 
                                    f"{os.path.splitext(os.path.basename(file_path))[0]}_chunk{i}.md")
            
            # Save both original chunk and summary for debugging
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(f"=== ORIGINAL CHUNK ===\n{chunk}\n\n")
                f.write(f"=== SUMMARY ===\n{summary}\n")
                
            print(f"Saved chunk {i} analysis to {chunk_path}")
    
    # Combine results
    if title_author and chunk_summaries:
        combined_summary = f"{title_author}\n\n" + '\n\n'.join(chunk_summaries)
        # Save combined summary before final processing
        os.makedirs("markdown/combined_chanks", exist_ok=True)
        combined_path = os.path.join("markdown/combined_chanks", 
                                   f"{os.path.splitext(os.path.basename(file_path))[0]}_combined.md")
        with open(combined_path, 'w', encoding='utf-8') as f:
            f.write(combined_summary)
            
        # Process combined summary
        final_summary = await summarize_chunk(combined_summary, combine_system_message)
        return final_summary
    
    return None

def save_summary(summary, output_path):
    """Save final summary to file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(summary)

async def process_all_md_files():
    """Process all Markdown files in the directory"""
    os.makedirs("summaries", exist_ok=True)
    os.makedirs("markdown/archive", exist_ok=True)
    os.makedirs("markdown/archive_chanks", exist_ok=True)
    
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
