#GameUploader.py

import os
import json
import glob
from dotenv import load_dotenv
import requests
from pathlib import Path
import mimetypes
import sys
import shutil
import time

load_dotenv()

# Допустимые MIME-типы изображений согласно схеме коллекции
ALLOWED_IMAGE_MIME_TYPES = [
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp', 
    'image/avif',
    'image/svg+xml'
]

# Соответствие расширений файлов MIME-типам
EXTENSION_TO_MIME = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.avif': 'image/avif',
    '.svg': 'image/svg+xml'
}

class AuthorManager:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.authors_cache = {}  # Кэш авторов: имя -> id
        
    def load_authors(self):
        """Загружает всех авторов из API"""
        try:
            if not self.token:
                raise Exception("Not authenticated")
                
            headers = {
                'Authorization': self.token
            }
            
            # Получаем всех авторов (с пагинацией)
            all_authors = []
            page = 1
            per_page = 200
            
            while True:
                response = requests.get(
                    f'{self.base_url}/collections/authors/records',
                    headers=headers,
                    params={'page': page, 'perPage': per_page}
                )
                response.raise_for_status()
                
                data = response.json()
                authors_chunk = data.get('items', [])
                all_authors.extend(authors_chunk)
                
                # Проверяем, есть ли еще страницы
                if len(authors_chunk) < per_page:
                    break
                    
                page += 1
            
            print(f'Downloaded {len(all_authors)} existing authors')
            
            # Создаем словарь для быстрого поиска авторов по имени
            for author in all_authors:
                self.authors_cache[author['name'].lower()] = author['id']
            
            return all_authors
        except Exception as e:
            print(f'Error getting existing authors: {e}')
            return []
    
    def create_author(self, name, description=""):
        """Создает нового автора"""
        try:
            if not self.token:
                raise Exception("Not authenticated")
                
            headers = {
                'Authorization': self.token
            }
            
            response = requests.post(
                f'{self.base_url}/collections/authors/records',
                headers=headers,
                json={
                    'name': name,
                    'description': description
                }
            )
            response.raise_for_status()
            
            author_data = response.json()
            print(f'Created author: {name} with ID: {author_data["id"]}')
            
            # Обновляем кэш
            self.authors_cache[name.lower()] = author_data["id"]
            
            return author_data["id"]
        except Exception as e:
            print(f'Error creating author "{name}": {e}')
            return None
    
    def get_or_create_author(self, name, description=""):
        """Получает ID автора по имени или создает нового"""
        name_lower = name.lower()
        
        # Проверяем кэш
        if name_lower in self.authors_cache:
            return self.authors_cache[name_lower]
        
        # Если автора нет в кэше, создаем нового
        return self.create_author(name, description)

class TagManager:
    def __init__(self):
        self.base_url = 'https://cyoa.cafe/api'
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.token = None
        self.category_id = "phc2n4pqe7hxe36"  # ID категории Custom
        self.existing_tags = {}  # Словарь для хранения существующих тегов (имя -> {id, description})
        
    def login(self):
        """Авторизация в API"""
        try:
            response = requests.post(
                f'{self.base_url}/collections/users/auth-with-password',
                json={
                    'identity': self.email,
                    'password': self.password
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data['token']
            print('Successfully logged in')
            return True
        except Exception as e:
            print(f'Login error: {e}')
            return False
    
    def get_all_tags(self):
        """Получение всех существующих тегов"""
        try:
            if not self.token:
                raise Exception("Not authenticated")
                
            headers = {
                'Authorization': self.token
            }
            
            # Получаем все теги (может потребоваться пагинация для большего количества)
            all_tags = []
            page = 1
            per_page = 200
            
            while True:
                response = requests.get(
                    f'{self.base_url}/collections/tags/records',
                    headers=headers,
                    params={'page': page, 'perPage': per_page}
                )
                response.raise_for_status()
                
                data = response.json()
                tags_chunk = data.get('items', [])
                all_tags.extend(tags_chunk)
                
                # Проверяем, есть ли еще страницы
                if len(tags_chunk) < per_page:
                    break
                    
                page += 1
            
            print(f'Downloaded {len(all_tags)} existing tags')
            
            # Создаем словарь для быстрого поиска тегов по имени
            for tag in all_tags:
                # Приводим все имена к нижнему регистру для нечувствительного к регистру поиска
                tag_name_lower = tag['name'].lower()
                self.existing_tags[tag_name_lower] = {
                    'id': tag['id'],
                    'name': tag['name'],  # Сохраняем оригинальное имя
                    'description': tag.get('description', '')
                }
            
            return all_tags  # Возвращаем полный список для использования в других функциях
        except Exception as e:
            print(f'Error getting existing tags: {e}')
            return []
    
    def create_tag(self, name, description=""):
        """Создание нового тега"""
        try:
            if not self.token:
                raise Exception("Not authenticated")
                
            headers = {
                'Authorization': self.token
            }
            
            response = requests.post(
                f'{self.base_url}/collections/tags/records',
                headers=headers,
                json={
                    'name': name,
                    'description': description
                }
            )
            response.raise_for_status()
            
            tag_data = response.json()
            print(f'Created tag: {name} with ID: {tag_data["id"]}')
            
            # Обновляем локальный словарь тегов
            self.existing_tags[name.lower()] = {
                'id': tag_data["id"],
                'name': name,
                'description': description
            }
            
            # Добавляем тег в категорию Custom
            self.add_tag_to_category(tag_data["id"])
            
            return tag_data["id"]
        except Exception as e:
            print(f'Error creating tag "{name}": {e}')
            return None
    
    def add_tag_to_category(self, tag_id):
        """Добавление тега в категорию Custom"""
        try:
            if not self.token:
                raise Exception("Not authenticated")
                
            headers = {
                'Authorization': self.token
            }
            
            # Сначала получаем текущие данные категории
            response = requests.get(
                f'{self.base_url}/collections/tag_categories/records/{self.category_id}',
                headers=headers
            )
            response.raise_for_status()
            
            category_data = response.json()
            current_tags = category_data.get('tags', [])
            
            # Добавляем новый тег, если его еще нет
            if tag_id not in current_tags:
                current_tags.append(tag_id)
                
                # Обновляем категорию
                response = requests.patch(
                    f'{self.base_url}/collections/tag_categories/records/{self.category_id}',
                    headers=headers,
                    json={
                        'tags': current_tags
                    }
                )
                response.raise_for_status()
                print(f'Added tag {tag_id} to category Custom')
                return True
            else:
                print(f'Tag {tag_id} already in category Custom')
                return True
        except Exception as e:
            print(f'Error adding tag {tag_id} to category: {e}')
            return False
    
    def get_or_create_tag(self, tag_name):
        """Получение ID тега по имени или создание нового, если тег не существует"""
        tag_name_lower = tag_name.lower()
        
        # Проверяем, существует ли тег
        if tag_name_lower in self.existing_tags:
            return self.existing_tags[tag_name_lower]['id']
        
        # Если тег не существует, создаем новый
        return self.create_tag(tag_name)


class GameUploader:
    def __init__(self):
        self.base_url = 'https://cyoa.cafe/api'
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.token = None
        self.tag_manager = TagManager()
        self.author_manager = None  # Будет инициализирован после логина
        self.request_delay = 3  # Задержка между запросами в секундах

    def login(self):
        try:
            response = requests.post(
                f'{self.base_url}/collections/users/auth-with-password',
                json={
                    'identity': self.email,
                    'password': self.password
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data['token']
            print('Successfully logged in')
            
            # Также выполняем логин для менеджера тегов
            self.tag_manager.login()
            
            # Загружаем все существующие теги
            self.tag_manager.get_all_tags()
            
            # Инициализируем менеджер авторов
            self.author_manager = AuthorManager(self.base_url, self.token)
            self.author_manager.load_authors()
            
            return data
        except Exception as e:
            print(f'Login error: {e}')
            return None



    def create_game(self, game_data):
        game_data['img_or_link'] = game_data['img_or_link'].lower()
        try:
            if not self.token:
                raise Exception("Not authenticated")

            headers = {
                'Authorization': self.token
            }

            # Проверяем наличие изображения (обложки)
            image_path = Path(game_data['image'])
            if not image_path.exists():
                raise FileNotFoundError(f"Cover image not found: {image_path}")

            # Определяем MIME-тип изображения
            file_ext = image_path.suffix.lower()
            mime_type = EXTENSION_TO_MIME.get(file_ext)
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(str(image_path))
                
            # Проверяем, что MIME-тип допустимый
            if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
                raise ValueError(f"Unsupported image format: {mime_type}. Supported formats: {', '.join(ALLOWED_IMAGE_MIME_TYPES)}")

            # Преобразуем имена тегов в ID тегов
            tag_ids = []
            if game_data.get('tags'):
                for tag_name in game_data['tags']:
                    tag_id = self.tag_manager.get_or_create_tag(tag_name)
                    if tag_id:
                        tag_ids.append(tag_id)
                    else:
                        print(f"Warning: Failed to get or create tag '{tag_name}'")

            # Создаем multipart form-data
            form_data = []  # Используем список кортежей вместо словаря
            
            # Добавляем базовые поля
            form_data.append(('title', game_data['title']))
            form_data.append(('description', game_data['description']))
            form_data.append(('img_or_link', game_data['img_or_link']))
            form_data.append(('uploader', game_data['uploader']))

            # Добавляем автора, если он указан
            if 'author' in game_data:
                author_id = self.author_manager.get_or_create_author(game_data['author'])
                if author_id:
                    # После создания игры мы добавим связь с автором отдельным запросом
                    print(f"Will link game to author: {game_data['author']} (ID: {author_id})")

            # Добавляем iframe_url только если это "link"-игра
            if game_data['img_or_link'] == 'link' and game_data.get('iframe_url'):
                form_data.append(('iframe_url', game_data['iframe_url']))

            # Добавляем теги как отдельные поля
            for tag_id in tag_ids:
                form_data.append(('tags', tag_id))

            # Открываем файл изображения для обложки
            cover_image_file = open(image_path, 'rb')
            
            files = {
                'image': ('blob', cover_image_file, mime_type)
            }
            
            # Если это игра с изображениями, добавляем страницы CYOA
            if game_data['img_or_link'] == 'img' and game_data.get('cyoa_pages'):
                for i, page_path in enumerate(game_data['cyoa_pages']):
                    page_path_obj = Path(page_path)
                    if page_path_obj.exists():
                        # Определяем MIME-тип страницы
                        page_ext = page_path_obj.suffix.lower()
                        page_mime_type = EXTENSION_TO_MIME.get(page_ext)
                        if not page_mime_type:
                            page_mime_type, _ = mimetypes.guess_type(str(page_path_obj))
                            
                        # Проверяем, что MIME-тип допустимый
                        if page_mime_type not in ALLOWED_IMAGE_MIME_TYPES:
                            print(f"Warning: Unsupported image format for page {page_path}: {page_mime_type}. Skipping.")
                            continue
                            
                        page_file = open(page_path_obj, 'rb')
                        files[f'cyoa_pages[{i}]'] = (f'page_{i}', page_file, page_mime_type)
                    else:
                        print(f"Warning: CYOA page not found: {page_path}")

            print("Form data:", form_data)
            print("Files:", {k: f"Binary content ({v[2]})" for k, v in files.items()})

            try:
                response = requests.post(
                    f'{self.base_url}/collections/games/records',
                    headers=headers,
                    data=form_data,
                    files=files
                )
                
                print(f"Status code: {response.status_code}")
                print(f"Response: {response.text}")
                
                response.raise_for_status()
                game_record = response.json()
                
                # Если был указан автор, связываем игру с автором
                if 'author' in game_data:
                    author_id = self.author_manager.get_or_create_author(game_data['author'])
                    if author_id:
                        # Добавляем задержку перед следующим запросом
                        time.sleep(self.request_delay)
                        self.link_game_to_author(game_record['id'], author_id)
                
                return game_record
            finally:
                # Закрываем файл обложки после отправки запроса
                cover_image_file.close()
                
                # Закрываем файлы страниц CYOA, если они были открыты
                if game_data['img_or_link'] == 'img' and game_data.get('cyoa_pages'):
                    for key in list(files.keys()):
                        if key.startswith('cyoa_pages'):
                            files[key][1].close()

        except Exception as e:
            print(f'Error creating game: {str(e)}')
            print(f'Error type: {type(e)}')
            raise
    
    def link_game_to_author(self, game_id, author_id):
        """Связывает игру с автором"""
        try:
            if not self.token:
                raise Exception("Not authenticated")
                
            headers = {
                'Authorization': self.token
            }
            
            # Сначала получаем текущие данные автора
            response = requests.get(
                f'{self.base_url}/collections/authors/records/{author_id}',
                headers=headers
            )
            response.raise_for_status()
            
            author_data = response.json()
            current_games = author_data.get('games', [])
            
            # Добавляем новую игру, если ее еще нет
            if game_id not in current_games:
                current_games.append(game_id)
                
                # Обновляем автора
                response = requests.patch(
                    f'{self.base_url}/collections/authors/records/{author_id}',
                    headers=headers,
                    json={
                        'games': current_games
                    }
                )
                response.raise_for_status()
                print(f'Linked game {game_id} to author {author_id}')
                return True
            else:
                print(f'Game {game_id} already linked to author {author_id}')
                return True
        except Exception as e:
            print(f'Error linking game {game_id} to author {author_id}: {e}')
            return False

def move_processed_files(game_data, processed_folder):
    """Перемещает обработанные файлы в указанную папку"""
    try:
        # Создаем папку для обработанных файлов, если она не существует
        if not os.path.exists(processed_folder):
            os.makedirs(processed_folder)
            print(f"Created folder for processed files: {processed_folder}")
        
        # Получаем базовое имя JSON файла
        json_path = None
        for file in os.listdir("New_Games"):
            if file.endswith(".json"):
                with open(os.path.join("New_Games", file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('title') == game_data['title']:
                        json_path = os.path.join("New_Games", file)
                        break
        
        if not json_path:
            print(f"Warning: Could not find JSON file for game {game_data['title']}")
            return False
        
        # Получаем имя JSON файла без пути
        json_filename = os.path.basename(json_path)
        base_name = os.path.splitext(json_filename)[0]
        
        # Перемещаем JSON файл
        shutil.move(json_path, os.path.join(processed_folder, json_filename))
        print(f"Moved JSON file: {json_filename}")
        
        # Перемещаем файл изображения обложки
        cover_path = game_data['image']
        cover_filename = os.path.basename(cover_path)
        shutil.move(cover_path, os.path.join(processed_folder, cover_filename))
        print(f"Moved cover image: {cover_filename}")
        
        # Если это игра с изображениями, перемещаем папку с CYOA страницами
        if game_data['img_or_link'] == 'img' and game_data.get('cyoa_pages'):
            pages_folder = os.path.join("New_Games", base_name)
            if os.path.isdir(pages_folder):
                # Создаем такую же папку в processed_folder
                processed_pages_folder = os.path.join(processed_folder, base_name)
                if not os.path.exists(processed_pages_folder):
                    os.makedirs(processed_pages_folder)
                
                # Перемещаем все файлы из папки страниц
                for page_file in os.listdir(pages_folder):
                    page_path = os.path.join(pages_folder, page_file)
                    if os.path.isfile(page_path):
                        shutil.move(page_path, os.path.join(processed_pages_folder, page_file))
                
                # Удаляем пустую исходную папку
                if len(os.listdir(pages_folder)) == 0:
                    os.rmdir(pages_folder)
                
                print(f"Moved CYOA pages folder: {base_name}")
        
        return True
    except Exception as e:
        print(f"Error moving processed files: {e}")
        return False

def load_games_from_folder(folder_path):
    """Загружает все JSON-файлы из указанной папки и их соответствующие изображения"""
    games = []
    
    # Получаем список всех JSON-файлов
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    
    for json_file in json_files:
        try:
            # Загружаем данные из JSON-файла
            with open(json_file, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
            
            # Получаем имя файла без расширения
            base_name = os.path.splitext(os.path.basename(json_file))[0]
            
            # Ищем соответствующее изображение для обложки (проверяем различные форматы)
            image_path = None
            
            for ext in EXTENSION_TO_MIME.keys():
                img_path = os.path.join(folder_path, f"{base_name}{ext}")
                if os.path.exists(img_path):
                    image_path = img_path
                    break
            
            if not image_path:
                print(f"Warning: Cover image not found for {json_file}")
                continue
            
            # Добавляем путь к изображению в game_data
            game_data['image'] = image_path
            
            # Добавляем необходимые поля, если их нет
            if 'img_or_link' not in game_data:
                # По умолчанию считаем, что это игра с изображениями
                game_data['img_or_link'] = "img"
            
            # Если это "link"-игра, проверяем наличие iframe_url
            if game_data['img_or_link'] == 'link' and 'iframe_url' not in game_data:
                print(f"Warning: iframe_url is missing for link-type game in {json_file}")
                continue
            
            # Если это "img"-игра, ищем CYOA страницы
            if game_data['img_or_link'] == 'img':
                # Проверяем, есть ли уже указанные страницы в JSON
                if 'cyoa_pages' not in game_data or not game_data['cyoa_pages']:
                    # Ищем страницы в папке с тем же именем, что и JSON файл
                    pages_folder = os.path.join(folder_path, base_name)
                    if os.path.isdir(pages_folder):
                        # Получаем список всех изображений в папке
                        page_files = []
                        for ext in EXTENSION_TO_MIME.keys():
                            page_files.extend(glob.glob(os.path.join(pages_folder, f"*{ext}")))
                        
                        # Сортируем файлы по имени
                        page_files.sort()
                        
                        if page_files:
                            game_data['cyoa_pages'] = page_files
                        else:
                            print(f"Warning: No CYOA pages found in folder {pages_folder} for {json_file}")
                    else:
                        print(f"Warning: CYOA pages folder {pages_folder} not found for {json_file}")
                
                # Если до сих пор нет страниц, пропускаем игру
                if 'cyoa_pages' not in game_data or not game_data['cyoa_pages']:
                    print(f"Warning: No CYOA pages specified for img-type game in {json_file}")
                    continue
            
            # Проверяем наличие поля uploader
            if 'uploader' not in game_data:
                game_data['uploader'] = "mar1q123caruaaw"  # значение по умолчанию из примера
            
            games.append(game_data)
            print(f"Loaded game: {game_data['title']} ({game_data['img_or_link']})")
            
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return games
 
def main():
    uploader = GameUploader()
    # Папка для перемещения обработанных файлов
    processed_folder = "Processed_Games"
    
    try:
        auth_data = uploader.login()
        if not auth_data:
            raise Exception("Failed to login")
        
        # Загружаем игры из папки New_Games
        games = load_games_from_folder("New_Games")
        
        print(f"Found {len(games)} games to upload")
        
        # Загружаем каждую игру
        for i, game_data in enumerate(games):
            try:
                print(f"Uploading {game_data['title']}...")
                record = uploader.create_game(game_data)
                print(f"Successfully uploaded: {game_data['title']}")
                
                # Перемещаем обработанные файлы
                if move_processed_files(game_data, processed_folder):
                    print(f"Files for {game_data['title']} moved to {processed_folder}")
                
                # Добавляем задержку перед следующей загрузкой (кроме последней)
                if i < len(games) - 1:
                    print(f"Waiting {uploader.request_delay} seconds before next upload...")
                    time.sleep(uploader.request_delay)
                
            except Exception as e:
                print(f"Failed to upload {game_data.get('title', 'Unknown')}: {e}")
        
    except Exception as e:
        print(f'Critical error: {e}')

if __name__ == "__main__":
    main()