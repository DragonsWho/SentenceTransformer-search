import requests
import numpy as np
import json
import torch
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

# Конфигурация API
API_URL = "https://api-inference.huggingface.co/models/BAAI/bge-large-en-v1.5"
headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

# Загрузка базы данных
print("Loading database...")
with open('search_data.json', 'r') as f:
    data = json.load(f)

embeddings = np.array(data['embeddings']['data']).reshape(data['embeddings']['shape'])
metadata = data['metadata']

print(f"Loaded embeddings shape: {embeddings.shape}")
print(f"Number of metadata entries: {len(metadata)}")
print(f"Sample metadata entry: {metadata[0]}")

def search(search_text, top_k=5):
    # Добавляем префикс для лучшего качества
    search_text = f"Represent this sentence for searching relevant passages: {search_text}"
    
    try:
        print(f"Sending request for text: {search_text}")
        response = query({
            "inputs": search_text,
            "options": {
                "wait_for_model": True
            }
        })
        print(f"API Response type: {type(response)}")
        print(f"API Response preview: {str(response)[:100]}...")
        
        if isinstance(response, dict) and 'error' in response:
            raise ValueError(f"API Error: {response['error']}")
            
        if isinstance(response, list) and len(response) == 1024:
            # Преобразуем в тензор и проверяем размерность
            query_embedding = torch.tensor(response).float().view(1, -1)
            print(f"Query embedding shape: {query_embedding.shape}")
            print(f"Query embedding norm: {torch.norm(query_embedding)}")
            if query_embedding.shape != (1, 1024):
                raise ValueError(f"Unexpected embedding shape: {query_embedding.shape}")
        else:
            raise ValueError(f"Unexpected API response format: {response}")
            
    except Exception as e:
        print(f"Error during API request: {str(e)}")
        return []
    
    # Преобразование эмбеддингов в тензор
    embeddings_tensor = torch.tensor(embeddings).float()
    print(f"Embeddings tensor shape: {embeddings_tensor.shape}")
    
    # Нормализация векторов
    query_embedding_norm = torch.nn.functional.normalize(query_embedding, p=2, dim=1)
    embeddings_norm = torch.nn.functional.normalize(embeddings_tensor, p=2, dim=1)
    
    # Вычисление косинусного сходства
    scores = torch.mm(query_embedding_norm, embeddings_norm.t()).squeeze()
    
    # Формирование результатов
    results = []
    for idx, score in enumerate(scores):
        results.append({
            'project': metadata[idx]['project'],
            'file': metadata[idx].get('file', ''),
            'score': float(score)
        })
    
    # Сортировка и возврат топ-K результатов
    return sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]

def format_results(results):
    if not results:
        return "Ничего не найдено или произошла ошибка."
    
    output = "Результаты поиска:\n" + "=" * 50 + "\n"
    for i, result in enumerate(results, 1):
        output += f"{i}. {result['project']}\n"
        output += f"   Файл: {result['file']}\n"
        output += f"   Сходство: {result['score']:.4f}\n"
        output += "-" * 50 + "\n"
    return output

def main():
    print("Semantic Search System")
    print("=" * 50)
    while True:
        search_query = input("\nВведите поисковый запрос (или 'exit' для выхода): ").strip()
        
        if search_query.lower() in ['exit', 'quit', 'q']:
            print("Завершение работы...")
            break
            
        if not search_query:
            print("Запрос не может быть пустым!")
            continue
            
        print("\nПоиск...")
        results = search(search_query)
        print(format_results(results))

if __name__ == "__main__":
    main()окей, напиши readme с описанием фаункций файлов.
