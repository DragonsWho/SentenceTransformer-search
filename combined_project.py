import os

# Список относительных путей к файлам
file_paths = [
    "components/grok3_api.py",
    "components/api_authors.py",
    "components/api_tags.py",
    "components/crawler.py",
    "components/game_checker.py",
    "components/js_json_extractor.py",
    "components/traffic_analyzer.py",
    "components/vector_search.py",
    "controller.py",
    "GameUploader.py",
    "get_screenshoot_puppy.js",
    "prepare_and_upload.py",
    "summarize.py",
    "components/project_downloader.py",
    "vision_query.py"
]

def combine_files(output_filename="combined_project.txt"):
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for file_path in file_paths:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                print(f"Файл {file_path} не найден, пропускаю...")
                continue
                
            # Определяем расширение файла
            ext = os.path.splitext(file_path)[1].lower()
            
            # Записываем разделитель и путь к файлу
            outfile.write(f"\n{'='*50}\n")
            outfile.write(f"File: {file_path}\n")
            outfile.write(f"{'='*50}\n\n")
            
            try:
                # Читаем и записываем содержимое файла
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(content)
                    outfile.write("\n")
                print(f"Успешно добавлен {file_path}")
            except Exception as e:
                print(f"Ошибка при обработке {file_path}: {str(e)}")

if __name__ == "__main__":
    # Создаем combined_project.txt в текущей директории
    combine_files()
    print("\nГотово! Файл combined_project.txt создан.")