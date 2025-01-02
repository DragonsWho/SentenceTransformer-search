import os
import json
import numpy as np
import requests
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_URL = "https://api-inference.huggingface.co/models/BAAI/bge-large-en-v1.5"
headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def generate_embeddings(text):
    """Generate embeddings for text using Hugging Face API"""
    response = query({
        "inputs": text,
        "options": {
            "wait_for_model": True
        }
    })
    return np.array(response)

def process_single_file(file_path, url=None):
    """Process a single markdown file and return its embeddings and metadata"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        embeddings = generate_embeddings(md_content)
        filename = os.path.basename(file_path)
        metadata = {
            'project': filename[:-3],  # Remove .md extension
            'file': filename,
            'url': url
        }
        return embeddings, metadata
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None, None

def process_all_files():
    """Process all markdown files in summaries directory"""
    md_dir = 'summaries'
    all_embeddings = []
    all_metadata = []
    
    for filename in os.listdir(md_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(md_dir, filename)
            embeddings, metadata = process_single_file(file_path)
            if embeddings is not None:
                all_embeddings.append(embeddings)
                all_metadata.append(metadata)
    
    return all_embeddings, all_metadata

def update_database(file_path, url):
    """Update database with a single file"""
    # Load existing data
    try:
        with open('search_data.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = {
            'embeddings': {
                'data': [],
                'shape': [0, 0]
            },
            'metadata': []
        }
    
    # Process new file
    embeddings, metadata = process_single_file(file_path, url)
    if embeddings is None:
        return False
    
    # Update embeddings
    existing_embeddings = np.array(existing_data['embeddings']['data']).reshape(
        existing_data['embeddings']['shape'])
    
    if existing_embeddings.size > 0:
        updated_embeddings = np.vstack([existing_embeddings, embeddings])
    else:
        updated_embeddings = np.array([embeddings])
    
    # Update metadata
    existing_data['metadata'].append(metadata)
    
    # Save updated data
    updated_data = {
        'embeddings': {
            'data': updated_embeddings.flatten().tolist(),
            'shape': list(updated_embeddings.shape)
        },
        'metadata': existing_data['metadata']
    }
    
    with open('search_data.json', 'w', encoding='utf-8') as f:
        json.dump(updated_data, f)
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Process markdown files for search database')
    parser.add_argument('--update', nargs=2, metavar=('FILE', 'URL'),
                       help='Update database with a single file and URL')
    parser.add_argument('--init', action='store_true',
                       help='Initialize database by processing all files in summaries folder')
    
    args = parser.parse_args()
    
    if args.init:
        # Initialize database mode
        all_embeddings, all_metadata = process_all_files()
        
        if not all_embeddings:
            print("No valid files found in summaries folder")
            return
            
        # Convert embeddings to numpy array
        embeddings_array = np.array(all_embeddings)
        
        # Save combined data in JSON format
        combined_data = {
            'embeddings': {
                'data': embeddings_array.flatten().tolist(),
                'shape': list(embeddings_array.shape)
            },
            'metadata': all_metadata
        }
        
        with open('search_data.json', 'w', encoding='utf-8') as f:
            json.dump(combined_data, f)
        print("Database initialized successfully with all summaries")
        
    elif args.update:
        # Update mode
        file_path, url = args.update
        if update_database(file_path, url):
            print(f"Successfully updated database with {file_path}")
        else:
            print(f"Failed to update database with {file_path}")
    else:
        print("Please specify a mode: --init to create new database or --update to add new entries")

if __name__ == "__main__":
    main()
