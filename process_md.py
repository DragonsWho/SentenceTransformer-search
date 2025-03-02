import os
import numpy as np
import argparse
import logging
import sys
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - process_md.py - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

# Load environment variables
load_dotenv()

# API configuration
API_KEY = os.getenv('DEEPINFRA_API_KEY')
MODEL_NAME = "BAAI/bge-en-icl"  # Default model
USE_M3_MODEL = False  # Flag for switching to M3 model
CHROMA_DIR = "chroma_db"  # Directory for storing ChromaDB

if not API_KEY:
    logger.error("DEEPINFRA_API_KEY not found in environment variables or .env file")
    logger.error("Please set this value in your .env file or environment")
    sys.exit(1)

# Initialize DeepInfra client
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepinfra.com/v1/openai",
)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

# Global variable for the collection
collection = None

def init_collection():
    """Initializes the collection with the correct distance settings"""
    global collection
    collection_name = "cyoa_games_m3" if USE_M3_MODEL else "cyoa_games"
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
        logger.info(f"Connected to existing ChromaDB collection '{collection_name}'")
    except:
        logger.info(f"Creating new ChromaDB collection '{collection_name}'")
        collection = chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  
        )
    
    return collection

def reset_collection():
    """Resets the collection and creates a new one with the correct settings"""
    global collection
    collection_name = "cyoa_games_m3" if USE_M3_MODEL else "cyoa_games"
    
    try:
        # Try to get and delete the old collection
        chroma_client.delete_collection(collection_name)
        logger.info("Deleted existing collection")
    except Exception as e:
        logger.info(f"No existing collection to delete or error: {str(e)}")
    
    # Create a new collection with inner product (dot product)
    collection = chroma_client.create_collection(
        name=collection_name, 
        metadata={"hnsw:space": "cosine"}   
    )
    logger.info(f"Created new collection '{collection_name}' with inner product distance")
    return collection

def generate_embeddings(text, is_query=False):
    """Generate embeddings for text using DeepInfra API with normalization"""
    logger.info(f"Generating embeddings for {'query' if is_query else 'document'} using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}")
    
    try:
        # Different handling for ICL vs M3 models
        if USE_M3_MODEL:
            # For M3 model, we don't use ICL examples
            if is_query:
                formatted_text = f"Represent this query for retrieving relevant CYOA games: {text}"
            else:
                formatted_text = f"Represent this CYOA game document for retrieval: {text}"
        else:
            # For ICL model, we use examples for queries
            if is_query:
                # Extensive and diverse examples in English for ICL
                icl_examples = """
Example 1:
Query: "CYOA with character development"
Relevant game: "An interactive story where the hero gains new abilities and develops skills after each choice, with branching storylines based on character growth"

Example 2:
Query: "horror elements CYOA"
Relevant game: "A dark adventure with frightening elements where choices affect character survival and mental stability in a supernatural setting"

Example 3:
Query: "post-apocalyptic mutants"
Relevant game: "CYOA story about survival in a radioactive world where the protagonist can mutate and gain new abilities depending on player choices"

Example 4:
Query: "fantasy multiple endings"
Relevant game: "A magical adventure with a branched narrative where player actions lead to one of 12 possible finales depending on key decisions"

Example 5:
Query: "dystopian cyberpunk"
Relevant game: "Neo-noir CYOA in a dark future with corporate control, where the hero makes choices between personal gain and resisting the system"

Example 6:
Query: "love triangle adventure"
Relevant game: "A story developing relationships between three characters amid a dangerous journey, where romantic choices impact the ending"

Example 7:
Query: "detective investigation"
Relevant game: "CYOA in noir genre with murder investigation where player collects clues and interrogates suspects through dialogue choices"

Example 8:
Query: "space exploration scifi"
Relevant game: "An interstellar adventure where the player makes critical decisions about alien encounters and ship management in the unknown regions of space"

Example 9:
Query: "medieval kingdom politics"
Relevant game: "A throne succession CYOA where court intrigue and political alliances determine your rise or fall as potential ruler"

Example 10:
Query: "time travel paradox"
Relevant game: "A complex narrative where players navigate temporal anomalies, with choices in one timeline affecting events in others"

Find for: "{}"
""".format(text)
                
                formatted_text = icl_examples
            else:
                # For documents in ICL model
                formatted_text = f"Represent this CYOA game for retrieval: {text}"
        
        # Get the current model name based on the flag
        current_model = "BAAI/bge-m3" if USE_M3_MODEL else MODEL_NAME
        
        response = client.embeddings.create(
            model=current_model,
            input=formatted_text,
            encoding_format="float"
        )
        
        # Extract the embedding from the response
        embedding = response.data[0].embedding
        
        # Normalize the vector for cosine similarity
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:  # Check for division by zero
            normalized = embedding_array / norm
        else:
            normalized = embedding_array
        
        logger.info(f"Embedding dimension: {len(embedding)}")
        logger.info(f"Used {response.usage.prompt_tokens} tokens for embedding")
        
        return normalized.tolist()  # Return the normalized vector
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        logger.error("IMPORTANT: Failed to get embeddings from the API. Check your API key and access rights.")
        return None

def process_single_file(file_path, url=None):
    """Process a single markdown file and return its embeddings and metadata"""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None, None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        if not md_content.strip():
            logger.error(f"File is empty: {file_path}")
            return None, None
            
        logger.info(f"Content length: {len(md_content)} characters")
        
        embeddings = generate_embeddings(md_content, is_query=False)
        
        filename = os.path.basename(file_path)
        metadata = {
            'project': filename[:-3],  # Remove .md extension
            'file': filename,
            'url': url if url else "",
            'content': md_content[:1000]  # Save the beginning of the content for preview
        }
        logger.info(f"Successfully processed {file_path}")
        return embeddings, metadata
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return None, None

def process_all_files():
    """Process all markdown files in summaries directory and add to ChromaDB"""
    md_dir = 'summaries'
    success_count = 0
    
    logger.info(f"Processing all files in {md_dir}")
    
    if not os.path.exists(md_dir):
        logger.error(f"Directory not found: {md_dir}")
        return False
    
    files = [f for f in os.listdir(md_dir) if f.endswith('.md')]
    logger.info(f"Found {len(files)} .md files")
    
    # Clear the collection before initialization
    try:
        collection.delete(where={})
        logger.info("Cleared existing collection data")
    except Exception as e:
        logger.warning(f"Error clearing collection: {str(e)}")
    
    for filename in files:
        file_path = os.path.join(md_dir, filename)
        embeddings, metadata = process_single_file(file_path)
        
        if embeddings is not None:
            try:
                collection.add(
                    embeddings=[embeddings],
                    metadatas=[metadata],
                    documents=[metadata.get('content', "")],
                    ids=[f"game_{filename[:-3]}"]  # Use the filename as ID
                )
                success_count += 1
                logger.info(f"Added {filename} to ChromaDB")
            except Exception as e:
                logger.error(f"Error adding {filename} to ChromaDB: {str(e)}")
    
    logger.info(f"Successfully processed {success_count} out of {len(files)} files")
    return success_count > 0

def update_database(file_path, url):
    """Update database with a single file"""
    logger.info(f"Updating database with file: {file_path}")
    
    # Process new file
    embeddings, metadata = process_single_file(file_path, url)
    if embeddings is None:
        logger.error("IMPORTANT: Failed to generate embeddings for the file. Database update aborted.")
        return False
    
    # Get the filename to create an ID
    filename = os.path.basename(file_path)
    game_id = f"game_{filename[:-3]}"
    
    try:
        # Check if an entry with this ID already exists
        try:
            # Try to get the element with this ID
            existing = collection.get(ids=[game_id])
            if len(existing['ids']) > 0:
                # If it exists, delete the old entry
                logger.info(f"Entry with ID {game_id} already exists, updating...")
                collection.delete(ids=[game_id])
        except:
            logger.info(f"No existing entry with ID {game_id}")
        
        # Add the new entry
        collection.add(
            embeddings=[embeddings],
            metadatas=[metadata],
            documents=[metadata.get('content', "")],
            ids=[game_id]
        )
        
        logger.info(f"Successfully updated database with {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error updating ChromaDB: {str(e)}")
        return False

def search_similar_games(query_text, top_k=5):
    """Search for similar games based on a query"""
    logger.info(f"Searching for: '{query_text}' using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}")
    
    try:
        # Generate embedding for the query
        query_embedding = generate_embeddings(query_text, is_query=True)
        
        if query_embedding is None:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Perform the search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"]
        )
        
        # Process the results
        found_games = []
        if results and results['metadatas']:
            for i, (metadata, distance) in enumerate(zip(results['metadatas'][0], results['distances'][0])):
                found_games.append({
                    'project': metadata.get('project', 'Unknown'),
                    'file': metadata.get('file', 'Unknown'),
                    'url': metadata.get('url', ''),
                    'content_preview': metadata.get('content', '')[:200] + '...',
                    'similarity': float(distance)  # With inner product distance, this is the similarity
                })
        
        logger.info(f"Found {len(found_games)} similar games")
        return found_games
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        return []

def debug_similarity(query, top_k=5):
    """Debug the similarity calculation between a query and documents in the collection"""
    logger.info(f"Debug similarity for query: '{query}' using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}")
    
    try:
        # Get all documents in the collection
        all_data = collection.get()
        
        if not all_data or 'embeddings' not in all_data or not all_data['embeddings']:
            logger.error("No documents in collection")
            return []
        
        # Generate embedding for the query
        query_emb = generate_embeddings(query, is_query=True)
        
        if query_emb is None:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Manually calculate similarity
        similarities = []
        for i, doc_emb in enumerate(all_data["embeddings"]):
            # Calculate the dot product
            sim = np.dot(query_emb, doc_emb)
            similarities.append((
                all_data["metadatas"][i].get("project", "Unknown"), 
                all_data["metadatas"][i].get("file", "Unknown"),
                all_data["metadatas"][i].get("url", ""),
                sim
            ))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[3], reverse=True)
        
        # Convert to the same format as search results
        found_games = []
        for project, file, url, sim in similarities[:top_k]:
            found_games.append({
                'project': project,
                'file': file,
                'url': url,
                'content_preview': "...",  # Do not load content for debugging
                'similarity': sim
            })
        
        return found_games
    except Exception as e:
        logger.error(f"Error in debug similarity: {str(e)}")
        return []

def compare_embeddings(text1, text2):
    """Compare two texts directly and output their similarity"""
    logger.info(f"Comparing texts directly using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}")
    
    try:
        # Generate embeddings
        emb1 = generate_embeddings(text1, is_query=True)
        emb2 = generate_embeddings(text2, is_query=False)
        
        if emb1 is None or emb2 is None:
            logger.error("Failed to generate embeddings")
            return None
        
        # Calculate the dot product
        similarity = np.dot(emb1, emb2)
        
        logger.info(f"Direct similarity: {similarity}")
        return similarity
    except Exception as e:
        logger.error(f"Error comparing embeddings: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Process markdown files for search database')
    parser.add_argument('--update', nargs=2, metavar=('FILE', 'URL'),
                       help='Update database with a single file and URL')
    parser.add_argument('--init', action='store_true',
                       help='Initialize database by processing all files in summaries folder')
    parser.add_argument('--search', type=str,
                       help='Search for similar games')
    parser.add_argument('--reset', action='store_true',
                      help='Reset the collection with proper distance metrics')
    parser.add_argument('--debug', type=str,
                      help='Debug similarity calculation with a query')
    parser.add_argument('--compare', nargs=2, metavar=('TEXT1', 'TEXT2'),
                      help='Compare similarity between two texts directly')
    parser.add_argument('-M3', action='store_true',
                      help='Use BAAI/bge-m3 model instead of BGE-ICL')
    
    args = parser.parse_args()
    
    # Set the global model flag if M3 is requested
    global USE_M3_MODEL
    if args.M3:
        USE_M3_MODEL = True
        logger.info("Using BAAI/bge-m3 model")
    
    # Initialize the collection
    global collection
    collection = init_collection()
    
    # Check API connection
    logger.info("Checking API connection...")
    try:
        # Get the current model name based on the flag
        current_model = "BAAI/bge-m3" if USE_M3_MODEL else MODEL_NAME
        
        test_response = client.embeddings.create(
            model=current_model,
            input="test",
            encoding_format="float"
        )
        logger.info("API connection successful")
        logger.info(f"Embedding dimension: {len(test_response.data[0].embedding)}")
    except Exception as e:
        logger.error(f"API connection error: {str(e)}")
        logger.error("Without a valid API key, embeddings cannot be generated correctly.")
        return
    
    # Process arguments
    if args.reset:
        reset_collection()
        collection = init_collection()  # Update the global variable
        print(f"Collection reset successfully for {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}. Please re-add your data.")
    
    elif args.init:
        # Initialize database mode
        logger.info(f"Initializing database from all summaries using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}")
        if process_all_files():
            logger.info("Database initialized successfully with all summaries")
            print(f"Database initialized successfully with all summaries for {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}")
        else:
            logger.error("Failed to initialize database")
            print("Failed to initialize database")
    
    elif args.update:
        # Update mode
        file_path, url = args.update
        logger.info(f"Update mode: processing {file_path} with URL {url}")
        if update_database(file_path, url):
            logger.info(f"Successfully updated database with {file_path}")
            print(f"Successfully updated database with {file_path}")
        else:
            logger.error(f"Failed to update database with {file_path}")
            print(f"Failed to update database with {file_path}")
    
    elif args.search:
        # Search mode
        query = args.search
        logger.info(f"Search mode: looking for '{query}'")
        results = search_similar_games(query, top_k=5)
        
        if results:
            print(f"\nSearch Results (using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}):")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['project']} (Similarity: {result['similarity']:.2f})")
                print(f"   URL: {result['url']}")
                print(f"   Preview: {result['content_preview']}")
        else:
            print("No results found")
    
    elif args.debug:
        # Debug mode
        query = args.debug
        logger.info(f"Debug mode: testing similarity for '{query}'")
        results = debug_similarity(query, top_k=5)
        
        if results:
            print(f"\nDebug Similarity Results (manual calculation using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}):")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['project']} (Similarity: {result['similarity']:.4f})")
                print(f"   URL: {result['url']}")
        else:
            print("No results for debug similarity")
    
    elif args.compare:
        # Compare mode
        text1, text2 = args.compare
        logger.info(f"Compare mode: testing similarity between two texts")
        similarity = compare_embeddings(text1, text2)
        
        if similarity is not None:
            print(f"\nDirect similarity between texts (using {'BGE-M3' if USE_M3_MODEL else 'BGE-ICL'}): {similarity:.4f}")
        else:
            print("Failed to compare texts")
    
    else:
        message = "Please specify a mode: --init to create new database, --update to add new entries, --search to find similar games, --reset to recreate the collection, --debug to test similarity, or --compare to compare two texts directly. Use -M3 flag to switch to BAAI/bge-m3 model."
        logger.error(message)
        print(message)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"Critical error: {str(e)}")
        sys.exit(1)