# GameUploader_static.py

import os
import json
import requests
from pathlib import Path
import mimetypes
import sys
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/game_uploader_static.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_MIME_TYPES = [
    'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/avif', 'image/svg+xml'
]

EXTENSION_TO_MIME = {
    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.gif': 'image/gif', '.webp': 'image/webp', '.avif': 'image/avif', '.svg': 'image/svg+xml'
}

class AuthorManager:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.authors_cache = {}
        logger.info("AuthorManager initialized")

    def load_authors(self):
        logger.info("Loading existing authors from API")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
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
                if len(authors_chunk) < per_page:
                    break
                page += 1
            logger.info(f'Downloaded {len(all_authors)} existing authors')
            for author in all_authors:
                self.authors_cache[author['name'].lower()] = author['id']
            return all_authors
        except Exception as e:
            logger.error(f'Error getting existing authors: {e}')
            return []

    def create_author(self, name, description=""):
        logger.info(f"Creating new author: {name}")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
            response = requests.post(
                f'{self.base_url}/collections/authors/records',
                headers=headers,
                json={'name': name, 'description': description}
            )
            response.raise_for_status()
            author_data = response.json()
            logger.info(f'Created author: {name} with ID: {author_data["id"]}')
            self.authors_cache[name.lower()] = author_data["id"]
            return author_data["id"]
        except Exception as e:
            logger.error(f'Error creating author "{name}": {e}')
            return None

    def get_or_create_authors(self, authors, description=""):
        if not isinstance(authors, list):
            authors = [authors]
        author_ids = []
        for name in authors:
            if not name:
                logger.warning("Empty author name encountered, skipping")
                continue
            name_lower = name.lower()
            if name_lower in self.authors_cache:
                logger.info(f"Found existing author: {name} (ID: {self.authors_cache[name_lower]})")
                author_ids.append(self.authors_cache[name_lower])
            else:
                author_id = self.create_author(name, description)
                if author_id:
                    author_ids.append(author_id)
        return author_ids

class TagManager:
    def __init__(self):
        self.base_url = 'https://cyoa.cafe/api'
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.token = None
        self.category_id = "phc2n4pqe7hxe36"
        self.existing_tags = {}
        logger.info("TagManager initialized")

    def login(self):
        logger.info("Attempting TagManager login")
        try:
            response = requests.post(
                f'{self.base_url}/collections/users/auth-with-password',
                json={'identity': self.email, 'password': self.password}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data['token']
            logger.info('TagManager successfully logged in')
            return True
        except Exception as e:
            logger.error(f'TagManager login error: {e}')
            return False

    def get_all_tags(self):
        logger.info("Loading all existing tags")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
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
                if len(tags_chunk) < per_page:
                    break
                page += 1
            logger.info(f'Downloaded {len(all_tags)} existing tags')
            self.existing_tags = {tag['name'].lower(): tag['id'] for tag in all_tags}
            return all_tags
        except Exception as e:
            logger.error(f'Error getting existing tags: {e}')
            return []

    def create_tag(self, name, description=""):
        logger.info(f"Creating new tag: {name}")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
            response = requests.post(
                f'{self.base_url}/collections/tags/records',
                headers=headers,
                json={'name': name, 'description': description}
            )
            response.raise_for_status()
            tag_data = response.json()
            logger.info(f'Created tag: {name} with ID: {tag_data["id"]}')
            self.existing_tags[name.lower()] = tag_data["id"]
            self.add_tag_to_category(tag_data["id"])
            return tag_data["id"]
        except Exception as e:
            logger.error(f'Error creating tag "{name}": {e}')
            return None

    def add_tag_to_category(self, tag_id):
        logger.info(f"Adding tag {tag_id} to category Custom")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
            response = requests.get(
                f'{self.base_url}/collections/tag_categories/records/{self.category_id}',
                headers=headers
            )
            response.raise_for_status()
            category_data = response.json()
            current_tags = category_data.get('tags', [])
            if tag_id not in current_tags:
                current_tags.append(tag_id)
                response = requests.patch(
                    f'{self.base_url}/collections/tag_categories/records/{self.category_id}',
                    headers=headers,
                    json={'tags': current_tags}
                )
                response.raise_for_status()
                logger.info(f'Added tag {tag_id} to category Custom')
        except Exception as e:
            logger.error(f'Error adding tag {tag_id} to category: {e}')

    def get_or_create_tag(self, tag_name):
        tag_name_lower = tag_name.lower()
        if tag_name_lower in self.existing_tags:
            logger.info(f"Found existing tag: {tag_name} (ID: {self.existing_tags[tag_name_lower]})")
            return self.existing_tags[tag_name_lower]
        return self.create_tag(tag_name)

class GameUploaderStatic:
    def __init__(self):
        self.base_url = 'https://cyoa.cafe/api'
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.token = None
        self.tag_manager = TagManager()
        self.author_manager = None
        self.request_delay = 3
        logger.info("GameUploaderStatic initialized")

    def login(self):
        logger.info("Attempting to login")
        try:
            response = requests.post(
                f'{self.base_url}/collections/users/auth-with-password',
                json={'identity': self.email, 'password': self.password}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data['token']
            logger.info("Successfully logged in")
            self.tag_manager.login()
            self.tag_manager.get_all_tags()
            self.author_manager = AuthorManager(self.base_url, self.token)
            self.author_manager.load_authors()
            return data
        except Exception as e:
            logger.error(f'Login failed: {str(e)}')
            return None

    def load_and_enrich_game_data(self, json_path, game_folder):
        """Loads JSON and enriches it with paths to images from the folder."""
        logger.info(f"Loading and enriching game data from {json_path} with images from {game_folder}")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                game_data = json.load(f)

            # Set game type as "img"
            game_data['img_or_link'] = 'img'

            # Define paths
            folder_path = Path(game_folder)
            screenshots_folder = folder_path / "screenshots"
            screenshot_path = screenshots_folder / "screenshot.webp"
            screenshot_preview_path = screenshots_folder / "screenshot_preview.webp"
            preview_folder = folder_path / "preview"

            # Check for screenshot as cover image
            if not screenshot_path.exists():
                raise FileNotFoundError(f"Screenshot not found at: {screenshot_path}")
            game_data['image'] = str(screenshot_path)
            
            # Check for screenshot preview
            if screenshot_preview_path.exists():
                game_data['image_preview'] = str(screenshot_preview_path)
                logger.info(f"Found screenshot preview: {screenshot_preview_path}")
            else:
                logger.warning(f"Screenshot preview not found at: {screenshot_preview_path}")

            # Find images in the main folder for game pages
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.svg')
            images = sorted([
                f for f in folder_path.iterdir() 
                if f.suffix.lower() in image_extensions and f.is_file()
            ])

            if not images:
                raise ValueError(f"No images found in folder: {game_folder}")

            # Use all images from the main folder as pages
            game_data['cyoa_pages'] = [str(img) for img in images]
            
            # Find preview images
            if preview_folder.exists() and preview_folder.is_dir():
                preview_images = sorted([
                    f for f in preview_folder.iterdir() 
                    if f.suffix.lower() in image_extensions and f.is_file()
                ])
                
                if preview_images:
                    game_data['cyoa_pages_preview'] = [str(img) for img in preview_images]
                    logger.info(f"Found {len(preview_images)} preview images for pages")
                else:
                    logger.warning(f"No preview images found in folder: {preview_folder}")
            else:
                logger.warning(f"Preview folder not found at: {preview_folder}")

            logger.info(f"Enriched game data with image: {game_data['image']}, pages: {len(game_data['cyoa_pages'])}")
            return game_data
        except Exception as e:
            logger.error(f"Error enriching game data: {str(e)}")
            raise

    def create_game(self, game_data):
        logger.info(f"Creating static game: {game_data['title']}")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}

            # Проверяем обложку
            image_path = Path(game_data['image'])
            if not image_path.exists():
                raise FileNotFoundError(f"Cover image not found: {image_path}")
            mime_type = EXTENSION_TO_MIME.get(image_path.suffix.lower(), mimetypes.guess_type(str(image_path))[0])
            if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
                raise ValueError(f"Unsupported image format for cover: {mime_type}")

            # Проверяем превью обложки
            image_preview = None
            if 'image_preview' in game_data and game_data['image_preview']:
                image_preview_path = Path(game_data['image_preview'])
                if image_preview_path.exists():
                    image_preview_mime_type = EXTENSION_TO_MIME.get(
                        image_preview_path.suffix.lower(), 
                        mimetypes.guess_type(str(image_preview_path))[0]
                    )
                    image_preview = (image_preview_path, image_preview_mime_type)
                    logger.info(f"Using image preview: {image_preview_path}")

            # Проверяем страницы
            if 'cyoa_pages' not in game_data or not game_data['cyoa_pages']:
                raise ValueError("No CYOA pages provided for static game")
            
            page_files = []
            for page_path in game_data['cyoa_pages']:
                page_path_obj = Path(page_path)
                if not page_path_obj.exists():
                    logger.error(f"Game page not found: {page_path}")
                    continue
                page_mime_type = EXTENSION_TO_MIME.get(page_path_obj.suffix.lower(), mimetypes.guess_type(str(page_path_obj))[0])
                if page_mime_type not in ALLOWED_IMAGE_MIME_TYPES:
                    logger.warning(f"Skipping page {page_path} due to unsupported format: {page_mime_type}")
                    continue
                if page_path_obj.stat().st_size > 524288000:
                    logger.warning(f"Skipping page {page_path} due to size exceeding 500MB: {page_path_obj.stat().st_size}")
                    continue
                page_files.append((page_path_obj, page_mime_type))

            if not page_files:
                raise ValueError("No valid CYOA pages available after filtering")

            # Проверяем превью страниц
            page_preview_files = []
            if 'cyoa_pages_preview' in game_data and game_data['cyoa_pages_preview']:
                for preview_path in game_data['cyoa_pages_preview']:
                    preview_path_obj = Path(preview_path)
                    if not preview_path_obj.exists():
                        logger.warning(f"Page preview not found: {preview_path}")
                        continue
                    preview_mime_type = EXTENSION_TO_MIME.get(
                        preview_path_obj.suffix.lower(), 
                        mimetypes.guess_type(str(preview_path_obj))[0]
                    )
                    page_preview_files.append((preview_path_obj, preview_mime_type))
                
                if page_preview_files:
                    logger.info(f"Using {len(page_preview_files)} page previews")

            # Обрабатываем теги
            tag_ids = []
            if game_data.get('tags'):
                for tag_name in game_data['tags']:
                    tag_id = self.tag_manager.get_or_create_tag(tag_name)
                    if tag_id:
                        tag_ids.append(tag_id)
                    else:
                        logger.warning(f"Failed to get or create tag '{tag_name}'")

            # Обрабатываем авторов
            author_ids = []
            if 'author' in game_data:
                author_ids = self.author_manager.get_or_create_authors(game_data['author'])
                logger.info(f"Authors for game: {game_data['author']} (IDs: {author_ids})")

            # Формируем данные формы
            form_data = [
                ('title', game_data['title']),
                ('description', game_data['description']),
                ('img_or_link', 'img'),
                ('uploader', game_data.get('uploader', 'mar1q123caruaaw')),
            ]
            for tag_id in tag_ids:
                form_data.append(('tags', tag_id))
            for author_id in author_ids:
                form_data.append(('authors', author_id))

            # Подготавливаем файлы для загрузки
            files = [
                ('image', ('cover_image', open(image_path, 'rb'), mime_type))
            ]
            
            # Добавляем превью обложки, если есть
            if image_preview:
                files.append((
                    'image_preview', 
                    (image_preview[0].name, open(image_preview[0], 'rb'), image_preview[1])
                ))

            # Добавляем все страницы с ключом 'cyoa_pages'
            for i, (page_path_obj, page_mime_type) in enumerate(page_files):
                files.append(
                    ('cyoa_pages', (page_path_obj.name, open(page_path_obj, 'rb'), page_mime_type))
                )
                logger.info(f"Preparing to upload page {i+1}/{len(page_files)}: {page_path_obj.name}")
                
            # Добавляем все превью страниц с ключом 'cyoa_pages_preview'
            for i, (preview_path_obj, preview_mime_type) in enumerate(page_preview_files):
                files.append(
                    ('cyoa_pages_preview', (preview_path_obj.name, open(preview_path_obj, 'rb'), preview_mime_type))
                )
                logger.info(f"Preparing to upload page preview {i+1}/{len(page_preview_files)}: {preview_path_obj.name}")

            # Отправляем запрос
            logger.info(f"Sending POST request with {len(page_files)} CYOA pages and {len(page_preview_files)} page previews")
            response = requests.post(
                f'{self.base_url}/collections/games/records',
                headers=headers,
                data=form_data,
                files=files
            )
            response.raise_for_status()
            game_record = response.json()
            logger.info(f"Game created successfully: {game_record['id']}")
            logger.debug(f"Server response: {json.dumps(game_record, indent=2)}")

            # Проверяем, загружены ли страницы
            if 'cyoa_pages' not in game_record or not game_record['cyoa_pages']:
                logger.warning("CYOA pages appear to be missing in the server response")
            elif len(game_record['cyoa_pages']) != len(page_files):
                logger.warning(f"Expected {len(page_files)} CYOA pages, but got {len(game_record['cyoa_pages'])} in response")
                
            # Проверяем, загружены ли превью страниц
            if page_preview_files and ('cyoa_pages_preview' not in game_record or not game_record['cyoa_pages_preview']):
                logger.warning("CYOA page previews appear to be missing in the server response")
            elif page_preview_files and len(game_record['cyoa_pages_preview']) != len(page_preview_files):
                logger.warning(f"Expected {len(page_preview_files)} CYOA page previews, but got {len(game_record['cyoa_pages_preview'])} in response")

            # Связываем авторов с игрой
            for author_id in author_ids:
                time.sleep(self.request_delay)
                self.link_game_to_author(game_record['id'], author_id)

            return game_record
        except Exception as e:
            logger.error(f"Failed to create game '{game_data['title']}': {str(e)}", exc_info=True)
            raise
        finally:
            # Закрываем файлы в случае ошибки или успеха
            for key, value in files:
                if isinstance(value, tuple) and len(value) >= 2 and hasattr(value[1], 'close'):
                    value[1].close()

    def link_game_to_author(self, game_id, author_id):
        logger.info(f"Linking game {game_id} to author {author_id}")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
            response = requests.get(
                f'{self.base_url}/collections/games/records/{game_id}',
                headers=headers
            )
            response.raise_for_status()
            game_data = response.json()
            current_authors = game_data.get('authors', [])
            if author_id not in current_authors:
                current_authors.append(author_id)
                response = requests.patch(
                    f'{self.base_url}/collections/games/records/{game_id}',
                    headers=headers,
                    json={'authors': current_authors}
                )
                response.raise_for_status()
                logger.info(f'Linked game {game_id} to author {author_id}')
            response = requests.get(
                f'{self.base_url}/collections/authors/records/{author_id}',
                headers=headers
            )
            response.raise_for_status()
            author_data = response.json()
            current_games = author_data.get('games', [])
            if game_id not in current_games:
                current_games.append(game_id)
                response = requests.patch(
                    f'{self.base_url}/collections/authors/records/{author_id}',
                    headers=headers,
                    json={'games': current_games}
                )
                response.raise_for_status()
                logger.info(f'Updated author {author_id} with game {game_id}')
            return True
        except Exception as e:
            logger.error(f'Error linking game {game_id} to author {author_id}: {e}')
            return False

def main():
    if len(sys.argv) < 3:
        logger.error("Usage: python GameUploader_static.py <json_path> <game_folder>")
        sys.exit(1)

    json_path = sys.argv[1]
    game_folder = sys.argv[2]

    uploader = GameUploaderStatic()
    try:
        auth_data = uploader.login()
        if not auth_data:
            raise Exception("Failed to login")

        game_data = uploader.load_and_enrich_game_data(json_path, game_folder)
        record = uploader.create_game(game_data)
        logger.info(f"Successfully uploaded: {game_data['title']} (ID: {record['id']})")
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()