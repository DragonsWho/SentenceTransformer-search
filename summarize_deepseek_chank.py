import os
import time
import shutil
from dotenv import load_dotenv
import requests
import tiktoken

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
        return response.json()['choices'][0]['message']['content']
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
    first_chunk_system_message = """ANALYZE THIS TEXT CHUNK FOR NSFW CYOA GAME:
Format your response as a structured list.
Focus on NEW and UNIQUE elements in this chunk.
Be specific but concise - this is intermediate data.
Include details that players might search for later.
dont use technical terms but casual descriptions.
Include alternative terms for important elements.

Your task is to create a preliminary summarization of the NSFW CYOA section of the game text. Your report should be detailed, and in the future, a series of such reports on all pieces of the game will be processed to obtain the final summarization of the game. The objective of all work is to obtain a suitable summarization for use by transformer models for semantic search.

0.This is the very first section, the beginning of the game. Try to find the name of the game and the author's name and write them especially clearly at the beginning of the report.  Highlight them. 
1. Title: [exact game title]
2. Author: [creator name]
  


1. NARRATIVE ELEMENTS:
- Plot points and events
- Main characters and descriptions
- Relationships and dynamics
- Setting details and worldbuilding 
- Memorable or unique scenes
- Story branches or alternate paths

- chapter titles and brief descriptions

2. GAME MECHANICS:
- New gameplay features
- Special abilities or powers
- Character customization
- Stats/skills/attributes 

3. ADULT CONTENT & KINKS:
- New fetishes or kinks
- Sexual mechanics and systems
- Relationship/romance options
- Body modification
- Transformation elements
- Corruption/training mechanics
- Special sexual abilities
- Unique adult scenes

4. DISTINCTIVE FEATURES:
- Unique selling points 
- Memorable moments
- Unusual combinations
- Innovative elements
- Rare or unique kinks
- Creative approaches

5. SEARCHABLE ELEMENTS:
- Specific scene descriptions
- Unique situations
- Memorable dialogue
- Special abilities
- Distinctive features
- Unusual combinations
- Key phrases players might remember"""









    chunk_system_message = """ANALYZE THIS TEXT CHUNK FOR NSFW CYOA GAME:
Format your response as a structured list.
Focus on NEW and UNIQUE elements in this chunk.
Be specific but concise - this is intermediate data.
Include details that players might search for later.
dont use technical terms but casual descriptions.
Include alternative terms for important elements.

Your task is to create a preliminary summarization of the NSFW CYOA section of the game text. Your report should be detailed, and in the future, a series of such reports on all pieces of the game will be processed to obtain the final summarization of the game. The objective of all work is to obtain a suitable summarization for use by transformer models for semantic search.

1. NARRATIVE ELEMENTS:
- Plot points and events
- Main characters and descriptions
- Relationships and dynamics
- Setting details and worldbuilding 
- Memorable or unique scenes
- Story branches or alternate paths

- chapter titles and brief descriptions

2. GAME MECHANICS:
- New gameplay features
- Special abilities or powers
- Character customization
- Stats/skills/attributes 

3. ADULT CONTENT & KINKS:
- New fetishes or kinks
- Sexual mechanics and systems
- Relationship/romance options
- Body modification
- Transformation elements
- Corruption/training mechanics
- Special sexual abilities
- Unique adult scenes

4. DISTINCTIVE FEATURES:
- Unique selling points 
- Memorable moments
- Unusual combinations
- Innovative elements
- Rare or unique kinks
- Creative approaches

5. SEARCHABLE ELEMENTS:
- Specific scene descriptions
- Unique situations
- Memorable dialogue
- Special abilities
- Distinctive features
- Unusual combinations
- Key phrases players might remember"""








    combine_system_message = """  
You are an expert AI specializing in creating detailed, search-optimized game descriptions. Your task is to combine multiple partial summaries into a comprehensive, structured game description. Follow these guidelines:

1. Combine information from all partial summaries
2. Remove any duplicate information
3. Create a coherent narrative flow
4. Maintain all important details
5. Structure the final summary according to the standard format:
 
 Your task is to analyze games and create structured summaries that will be used by transformer models for semantic search. Generated content should be both human-readable and optimized for AI processing.

Take into account that the search will be performed using free-form user queries. Try to use search words that most accurately describe the game, its most memorable features. 

Don't write anything but summarize in the message, the response will be handled by the script and put entirely into the database. All the games in the base are CYOA, no need to mention this feature.

you can and should use the RIGHT names for kinks and features, even if they are dirty, lewd words. Accuracy of search is paramount. 

Create a comprehensive description following this exact structure:
 

 
Title: [game name] (Also generate 20 alternative search queries for the game "[game name]". Generate ONLY typing errors and misspellings for "[game name]". Must include:
1. Missing letter version (e.g. "recive" for "receive")
2. Double letter version (e.g. "recieve" for "receive")
3. Swapped adjacent letters (e.g. "recevie" for "receive")
4. No spaces version
5. Wrong similar-sounding letter (e.g. "resieve" for "receive")
6. Keyboard adjacent letter error (e.g. "receuve" for "receive")
7. Common autocorrect error
8. Phonetic misspelling
9. Split word error (extra space)
10. Merged words with next/previous word

Do not add genre tags, categories or content descriptions. Only output misspellings of the title itself.)
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
 

Themes and Tone:
- Main themes explored
- Emotional atmosphere
- Writing style
- Narrative approach

 

Common Search Patterns: (dont use word "CYOA") 
Write 7 different ways how users might try to find this game, including:

1. Memory-based queries (4 examples):
- "I remember game where [memorable scene/situation]"
- "looking for game with [distinct character/feature]"
- "there was this scene where [specific event]"
- Include common mistakes in names/terms

2. Emotional/Subjective searches (3 examples):
- "[emotional reaction] story about [theme]"
- "game that made me feel [emotion] when [event]"
- Use casual/colloquial language
 

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
