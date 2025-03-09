import json
from copy import deepcopy
from sklearn.cluster import DBSCAN
import numpy as np

# Функция для проверки формата координат
def validate_coordinates(coords, block_text):
    if not isinstance(coords, list) or len(coords) != 4:
        raise ValueError(f"Неверный формат координат для блока '{block_text}': {coords}. Ожидается список из 4 точек.")
    for point in coords:
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError(f"Неверный формат точки в координатах для блока '{block_text}': {point}. Ожидается [x, y].")
        if not all(isinstance(coord, (int, float)) for coord in point):
            raise ValueError(f"Координаты должны быть числами для блока '{block_text}': {point}.")

# Функция для вычисления центра координат
def get_center(coords):
    validate_coordinates(coords, "unknown")
    x_coords = [coords[0][0], coords[1][0], coords[2][0], coords[3][0]]
    y_coords = [coords[0][1], coords[1][1], coords[2][1], coords[3][1]]
    return [np.mean(x_coords), np.mean(y_coords)]

# Функция для вычисления ограничивающего прямоугольника (bounding box)
def calculate_bounding_box(coordinates_list):
    all_x = []
    all_y = []
    for coords in coordinates_list:
        validate_coordinates(coords, "unknown")
        all_x.extend([coords[0][0], coords[1][0], coords[2][0], coords[3][0]])
        all_y.extend([coords[0][1], coords[1][1], coords[2][1], coords[3][1]])
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    return [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]

# Функция для объединения текстовых блоков с использованием DBSCAN
def group_text_blocks(data):
    if "text_blocks" not in data:
        raise KeyError("В JSON отсутствует ключ 'text_blocks'.")
    
    text_blocks = deepcopy(data["text_blocks"])
    
    # Вычисляем центры для всех блоков
    centers = []
    blocks_with_centers = []
    for block in text_blocks:
        if "text" not in block or "coordinates" not in block:
            print(f"Пропущен блок {block} из-за отсутствия 'text' или 'coordinates'.")
            continue
        center = get_center(block["coordinates"])
        centers.append(center)
        blocks_with_centers.append(block)
    
    # Применяем DBSCAN для кластеризации
    X = np.array(centers)
    db = DBSCAN(eps=45, min_samples=1).fit(X)  # Уменьшен eps до 40, min_samples=2
    labels = db.labels_
    
    # Группируем блоки по кластерам
    grouped_blocks = []
    for label in set(labels):
        if label == -1:  # Шум (одиночные точки или заголовки)
            noise_blocks = [blocks_with_centers[i] for i in range(len(labels)) if labels[i] == label]
            for noise_block in noise_blocks:
                # Проверяем, является ли блок заголовком (длинная фраза)
                if len(noise_block["text"].split()) > 2:
                    grouped_blocks.append(noise_block)
                else:
                    # Одиночные слова добавляем как есть, если не шум
                    pass
            continue
        
        cluster_blocks = [blocks_with_centers[i] for i in range(len(labels)) if labels[i] == label]
        
        # Сортируем блоки в кластере по y, затем по x для естественного порядка
        cluster_blocks.sort(key=lambda x: (get_center(x["coordinates"])[1], get_center(x["coordinates"])[0]))
        
        # Объединяем текст
        combined_text = " ".join(block["text"] for block in cluster_blocks).strip()
        new_coords = calculate_bounding_box([block["coordinates"] for block in cluster_blocks])
        
        grouped_blocks.append({
            "text": combined_text,
            "coordinates": new_coords
        })
    
    return {"text_blocks": grouped_blocks}

# Основная логика
def process_json(input_file, output_file):
    try:
        # Читаем данные из input файла
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Группируем текст
        result = group_text_blocks(data)
        
        # Сохраняем результат в output файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        print(f"Обработка завершена. Результат сохранен в {output_file}")
    
    except FileNotFoundError:
        print(f"Ошибка: Файл {input_file} не найден.")
    except json.JSONDecodeError:
        print(f"Ошибка: Неверный формат JSON в файле {input_file}.")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

# Запуск обработки
if __name__ == "__main__":
    input_file = "text_data_test.json"
    output_file = "text_data.json"
    process_json(input_file, output_file)