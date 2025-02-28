# process_md.py

import os
import json
import numpy as np
import requests
import argparse
import logging
import sys
from dotenv import load_dotenv

# Настройка логирования
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
API_URL = "https://api-inference.huggingface.co/models/BAAI/bge-large-en-v1.5"
API_KEY = os.getenv('HF_API_KEY')

if not API_KEY:
    logger.error("HF_API_KEY not found in environment variables or .env file")
    logger.error("Please set this value in your .env file or environment")
    sys.exit(1)

headers = {"Authorization": f"Bearer {API_KEY}"}

def query(payload):
    """Make a request to the Hugging Face API with error handling"""
    try:
        logger.debug(f"Sending query to API: {API_URL}")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Проверка статус-кода
        if response.status_code == 401:
            logger.error("API key is invalid or expired. Please check your HF_API_KEY.")
            return {"error": "Authentication failed"}
        elif response.status_code == 503:
            logger.error("API service unavailable. The model might be loading or the service is down.")
            return {"error": "Service unavailable"}
        elif response.status_code != 200:
            logger.error(f"API returned error code {response.status_code}: {response.text}")
            return {"error": f"API error: {response.status_code}"}
        
        # Пытаемся получить JSON
        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse API response as JSON: {str(e)}")
            logger.error(f"Response content: {response.text[:200]}...")
            return {"error": "Invalid JSON response"}
            
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return {"error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        logger.error("Connection error. Please check your internet connection.")
        return {"error": "Connection error"}
    except Exception as e:
        logger.error(f"Unexpected error during API request: {str(e)}")
        return {"error": str(e)}

def generate_embeddings(text):
    """Generate embeddings for text using Hugging Face API"""
    logger.info("Generating embeddings for text")
    
    response = query({
        "inputs": text,
        "options": {
            "wait_for_model": True
        }
    })
    
    # ВАЖНО: не используем фиктивные вложения, чтобы не засорять базу данных
    # Проверка на ошибку в ответе
    if isinstance(response, dict) and "error" in response:
        logger.error(f"API returned error: {response['error']}")
        # Вместо запасного встраивания возвращаем None, чтобы прервать процесс
        logger.error("ВАЖНО: Не удалось получить вложения от API. Проверьте ваш API-ключ и права доступа.")
        return None
    
    # Преобразуем ответ в numpy массив
    try:
        embedding_array = np.array(response)
        logger.info(f"Embedding shape: {embedding_array.shape}")
        
        # Проверяем и исправляем форму массива
        if len(embedding_array.shape) == 1:
            logger.warning(f"Reshaping 1D embedding of size {embedding_array.shape[0]} to 2D")
            embedding_array = embedding_array.reshape(1, -1)
        
        return embedding_array
    except Exception as e:
        logger.error(f"Error processing embedding: {str(e)}")
        logger.error(f"API response: {response}")
        # ВАЖНО: не используем запасное встраивание, возвращаем None
        logger.error("ВАЖНО: Не удалось обработать ответ API. Запись не будет добавлена в базу данных.")
        return None

def process_single_file(file_path, url=None):
    """Process a single markdown file and return its embeddings and metadata"""
    logger.info(f"Processing file: {file_path}")
    
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None, None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        if not md_content.strip():
            logger.error(f"File is empty: {file_path}")
            return None, None
            
        logger.info(f"Content length: {len(md_content)} characters")
        
        embeddings = generate_embeddings(md_content)
        
        filename = os.path.basename(file_path)
        metadata = {
            'project': filename[:-3],  # Remove .md extension
            'file': filename,
            'url': url
        }
        logger.info(f"Successfully processed {file_path}")
        return embeddings, metadata
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return None, None

def process_all_files():
    """Process all markdown files in summaries directory"""
    md_dir = 'summaries'
    all_embeddings = []
    all_metadata = []
    
    logger.info(f"Processing all files in {md_dir}")
    
    if not os.path.exists(md_dir):
        logger.error(f"Directory not found: {md_dir}")
        return [], []
    
    files = [f for f in os.listdir(md_dir) if f.endswith('.md')]
    logger.info(f"Found {len(files)} .md files")
    
    for filename in files:
        file_path = os.path.join(md_dir, filename)
        embeddings, metadata = process_single_file(file_path)
        if embeddings is not None:
            all_embeddings.append(embeddings)
            all_metadata.append(metadata)
    
    logger.info(f"Successfully processed {len(all_embeddings)} out of {len(files)} files")
    return all_embeddings, all_metadata

def update_database(file_path, url):
    """Update database with a single file"""
    logger.info(f"Updating database with file: {file_path}")
    
    # Load existing data
    try:
        if os.path.exists('search_data.json'):
            logger.info(f"Loading existing search_data.json")
            with open('search_data.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # Проверяем формат данных
            if not ('embeddings' in existing_data and 'metadata' in existing_data):
                logger.error("Invalid search_data.json format")
                # Инициализируем заново
                existing_data = {
                    'embeddings': {
                        'data': [],
                        'shape': [0, 0]
                    },
                    'metadata': []
                }
        else:
            logger.info("search_data.json not found, initializing new database")
            existing_data = {
                'embeddings': {
                    'data': [],
                    'shape': [0, 0]
                },
                'metadata': []
            }
    except Exception as e:
        logger.error(f"Error loading search_data.json: {str(e)}")
        logger.info("Initializing new database")
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
        logger.error("ВАЖНО: Не удалось сгенерировать встраивания для файла. Обновление базы данных прервано.")
        return False
    
    # Логируем форму встраиваний для отладки
    logger.info(f"New embeddings shape: {embeddings.shape}")
    
    # Убедимся, что embeddings имеет правильную форму (2D)
    if len(embeddings.shape) == 1:
        logger.warning("Reshaping 1D embeddings to 2D")
        embeddings = embeddings.reshape(1, -1)
    
    # Update embeddings
    if existing_data['embeddings']['shape'][0] > 0:
        # Есть существующие данные
        existing_shape = existing_data['embeddings']['shape']
        logger.info(f"Existing embeddings shape: {existing_shape}")
        
        try:
            existing_embeddings = np.array(existing_data['embeddings']['data']).reshape(existing_shape)
            
            # Проверка совместимости размерностей
            if existing_embeddings.shape[1] != embeddings.shape[1]:
                logger.error(f"Dimension mismatch: existing={existing_embeddings.shape[1]}, new={embeddings.shape[1]}")
                logger.error("Cannot merge incompatible embeddings. Consider reinitializing the database.")
                return False
            
            logger.info("Merging with existing embeddings")
            updated_embeddings = np.vstack([existing_embeddings, embeddings])
        except Exception as e:
            logger.error(f"Error merging embeddings: {str(e)}")
            # Пытаемся восстановиться, используя только новые встраивания
            logger.warning("Using only new embeddings due to merge error")
            updated_embeddings = embeddings
    else:
        # Нет существующих данных
        logger.info("No existing embeddings, using new embeddings directly")
        updated_embeddings = embeddings
    
    # Update metadata
    existing_data['metadata'].append(metadata)
    
    # Save updated data
    try:
        updated_data = {
            'embeddings': {
                'data': updated_embeddings.flatten().tolist(),
                'shape': list(updated_embeddings.shape)
            },
            'metadata': existing_data['metadata']
        }
        
        with open('search_data.json', 'w', encoding='utf-8') as f:
            json.dump(updated_data, f)
        
        logger.info(f"Successfully updated database. New shape: {updated_embeddings.shape}")
        logger.info(f"Total entries in database: {len(updated_data['metadata'])}")
        return True
    except Exception as e:
        logger.error(f"Error saving updated data: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Process markdown files for search database')
    parser.add_argument('--update', nargs=2, metavar=('FILE', 'URL'),
                       help='Update database with a single file and URL')
    parser.add_argument('--init', action='store_true',
                       help='Initialize database by processing all files in summaries folder')
    
    args = parser.parse_args()
    
    # Проверка подключения к API
    logger.info("Checking API connection...")
    test_response = query({"inputs": "test", "options": {"wait_for_model": True}})
    if isinstance(test_response, dict) and "error" in test_response:
        if test_response["error"] == "Authentication failed":
            logger.error("API KEY IS INVALID! Please check your HF_API_KEY in .env file.")
            logger.error("Without a valid API key, embeddings cannot be generated correctly.")
            # Не выходим, так как у нас есть запасной вариант с возвращением фиктивных встраиваний
        else:
            logger.warning(f"API test returned an error: {test_response['error']}")
            logger.warning("Will attempt to continue with fallback embeddings if needed.")
    else:
        logger.info("API connection successful")
    
    if args.init:
        # Initialize database mode
        logger.info("Initializing database from all summaries")
        all_embeddings, all_metadata = process_all_files()
        
        if not all_embeddings:
            logger.error("No valid files found in summaries folder")
            return
            
        # Convert embeddings to numpy array
        try:
            embeddings_array = np.vstack(all_embeddings)
            logger.info(f"Combined embeddings shape: {embeddings_array.shape}")
            
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
            logger.info("Database initialized successfully with all summaries")
            print("Database initialized successfully with all summaries")
        except Exception as e:
            logger.error(f"Error creating database: {str(e)}")
            print(f"Failed to initialize database: {str(e)}")
        
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
    else:
        message = "Please specify a mode: --init to create new database or --update to add new entries"
        logger.error(message)
        print(message)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        print(f"Critical error: {str(e)}")
        sys.exit(1)