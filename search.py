from sentence_transformers import SentenceTransformer, util
import numpy as np
import json
import torch

# Загрузка модели
model = SentenceTransformer('all-MiniLM-L6-v2')

# Загрузка базы данных
with open('search_data.json', 'r') as f:
    data = json.load(f)

embeddings = np.array(data['embeddings']['data']).reshape(data['embeddings']['shape'])
metadata = data['metadata']

def search(query, top_k=5):
    # Кодирование запроса
    query_embedding = model.encode(query, convert_to_tensor=True).float().cpu()
    
    # Вычисление косинусного сходства
    embeddings_tensor = torch.tensor(embeddings).float().cpu()
    scores = util.cos_sim(query_embedding, embeddings_tensor)[0]
    
    # Сортировка результатов
    results = []
    for idx, score in enumerate(scores):
        results.append({
            'project': metadata[idx]['project'],
            'url': metadata[idx]['url'],
            'score': float(score)
        })
    
    # Возврат топ-K результатов
    return sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]

if __name__ == "__main__":
    query = input("Введите поисковый запрос: ")
    results = search(query)
    print("Результаты поиска:")
    for result in results:
        print(f"{result['project']} (сходство: {result['score']:.4f})")
        print(f"URL: {result['url']}\n")
