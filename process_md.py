import os
import json
import numpy as np
import requests
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

def process_md_files():
    """Process all markdown files and create search database"""
    md_dir = 'summaries'
    all_embeddings = []
    all_metadata = []
    
    # Process each markdown file
    for filename in os.listdir(md_dir):
        if filename.endswith('.md'):
            try:
                # Read markdown content
                with open(os.path.join(md_dir, filename), 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                # Generate embeddings and metadata
                embeddings = generate_embeddings(md_content)
                all_embeddings.append(embeddings)
                all_metadata.append({
                    'project': filename[:-3],  # Remove .md extension
                    'file': filename
                })
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
    
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

if __name__ == "__main__":
    process_md_files()
