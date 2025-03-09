from google.cloud import vision
import json
import os
import sys
import re

# Укажите путь к JSON-файлу с учетными данными
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_vision_API_for_OCR.json"

def format_json_output(json_string):
    """Форматирует JSON строку, делая координаты более компактными"""
    # Используем регулярное выражение для замены формата координат
    # Ищем все вхождения координат с множественными пробелами и переносами
    pattern = r'"coordinates": \[\s+\[\s+(\d+),\s+(\d+)\s+\],\s+\[\s+(\d+),\s+(\d+)\s+\],\s+\[\s+(\d+),\s+(\d+)\s+\],\s+\[\s+(\d+),\s+(\d+)\s+\]\s+\]'
    replacement = r'"coordinates": [ [\1, \2], [\3, \4], [\5, \6], [\7, \8] ]'
    
    return re.sub(pattern, replacement, json_string)

def detect_document_text_and_save(image_path, output_json="text_data.json"):
    try:
        # Проверяем существование файла
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")

        # Создаем клиент Vision API
        print(f"Создание клиента Vision API для {image_path}")
        client = vision.ImageAnnotatorClient()

        # Читаем изображение
        print(f"Чтение изображения: {image_path}")
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Выполняем распознавание текста
        print(f"Запуск распознавания текста для {image_path}")
        response = client.document_text_detection(image=image)

        # Проверяем наличие ошибок
        if response.error.message:
            raise Exception(f"Ошибка Vision API: {response.error.message}")

        # Структура для хранения данных
        text_data = {
            "image_path": image_path,
            "text_blocks": []
        }

        # Получаем полный текст и координаты
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                block_text = ""
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = "".join(symbol.text for symbol in word.symbols)
                        block_text += word_text + " "
                block_text = block_text.strip()

                # Получаем координаты блока
                vertices = block.bounding_box.vertices
                coordinates = [[v.x, v.y] for v in vertices]

                # Добавляем блок текста и координаты в структуру
                text_data["text_blocks"].append({
                    "text": block_text,
                    "coordinates": coordinates
                })

        # Конвертируем в строку JSON с отступами
        json_string = json.dumps(text_data, indent=4, ensure_ascii=False)
        
        # Применяем форматирование для компактных координат
        formatted_json = format_json_output(json_string)
        
        # Сохраняем данные в JSON
        print(f"Сохранение данных в {output_json}")
        with open(output_json, "w", encoding="utf-8") as f:
            f.write(formatted_json)

        print(f"Данные сохранены в {output_json}")

    except Exception as e:
        print(f"Ошибка в detect_document_text_and_save: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python ocr.py <image_path> <output_json>", file=sys.stderr)
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_json = sys.argv[2]
    detect_document_text_and_save(image_path, output_json)