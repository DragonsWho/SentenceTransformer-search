# replace_game_image.py

import os
import sys
import subprocess
import requests
import logging
from dotenv import load_dotenv
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/replace_game_image.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Константы
SCREENSHOTS_DIR = "screenshots"
API_BASE_URL = "https://cyoa.cafe/api"
PUPPETEER_SCRIPT = "get_screenshoot_puppy.js"
ALLOWED_MIME_TYPES = [
    "image/png", "image/jpeg", "image/gif", "image/webp", 
    "image/avif", "image/svg+xml"
]

load_dotenv()

class GameImageReplacer:
    def __init__(self):
        self.email = os.getenv('EMAIL')
        self.password = os.getenv('PASSWORD')
        self.token = None
        self.games_cache = {}
        logger.info("GameImageReplacer initialized")

    def login(self):
        """Аутентификация в API"""
        logger.info("Attempting to login")
        try:
            response = requests.post(
                f"{API_BASE_URL}/collections/users/auth-with-password",
                json={'identity': self.email, 'password': self.password}
            )
            response.raise_for_status()
            self.token = response.json()['token']
            logger.info("Successfully logged in")
            return True
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return False

    def load_all_games(self):
        """Загрузка всех игр с сервера"""
        logger.info("Loading all games from API")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
            all_games = []
            page = 1
            per_page = 200
            while True:
                response = requests.get(
                    f"{API_BASE_URL}/collections/games/records",
                    headers=headers,
                    params={'page': page, 'perPage': per_page}
                )
                response.raise_for_status()
                data = response.json()
                games_chunk = data.get('items', [])
                all_games.extend(games_chunk)
                if len(games_chunk) < per_page:
                    break
                page += 1
            self.games_cache = {game['title'].lower(): game for game in all_games}
            logger.info(f"Loaded {len(self.games_cache)} games")
            return True
        except Exception as e:
            logger.error(f"Error loading games: {str(e)}")
            return False

    def find_game_by_title(self, title):
        """Поиск игры по названию"""
        title_lower = title.lower()
        if title_lower in self.games_cache:
            logger.info(f"Found game: {title} (ID: {self.games_cache[title_lower]['id']})")
            return self.games_cache[title_lower]
        logger.warning(f"Game not found: {title}")
        return None

    def capture_screenshot(self, url):
        """Запуск Puppeteer для захвата скриншота"""
        logger.info(f"Capturing screenshot for URL: {url}")
        try:
            if not os.path.exists(PUPPETEER_SCRIPT):
                raise FileNotFoundError(f"Puppeteer script not found: {PUPPETEER_SCRIPT}")
            
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            result = subprocess.run(
                ["node", PUPPETEER_SCRIPT, url, "--pause"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Puppeteer output: {result.stdout}")
            
            # Предполагаем, что имя файла формируется из URL в get_screenshoot_puppy.js
            screenshot_name = url.rstrip('/').split('/')[-1] or url.split('//')[1].split('/')[0]
            screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{screenshot_name}.webp")
            
            if os.path.exists(screenshot_path):
                logger.info(f"Screenshot saved: {screenshot_path}")
                return screenshot_path
            else:
                logger.error("Screenshot file not found after Puppeteer execution")
                return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Puppeteer failed: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return None

    def replace_game_image(self, game_id, screenshot_path):
        """Замена изображения игры через API"""
        logger.info(f"Replacing image for game ID: {game_id}")
        try:
            if not self.token:
                raise Exception("Not authenticated")
            headers = {'Authorization': self.token}
            
            screenshot_path = Path(screenshot_path)
            if not screenshot_path.exists():
                raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")

            mime_type = "image/webp"  # Предполагаем, что Puppeteer сохраняет в .webp
            if mime_type not in ALLOWED_MIME_TYPES:
                raise ValueError(f"Unsupported mime type: {mime_type}")

            with open(screenshot_path, 'rb') as image_file:
                files = {'image': ('blob', image_file, mime_type)}
                response = requests.patch(
                    f"{API_BASE_URL}/collections/games/records/{game_id}",
                    headers=headers,
                    files=files
                )
                logger.debug(f"API response: {response.text}")
                response.raise_for_status()
            
            logger.info(f"Successfully replaced image for game ID: {game_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to replace image for game ID {game_id}: {str(e)}")
            return False

    def process_game(self, game_title):
        """Основной процесс обработки игры"""
        # Поиск игры
        game = self.find_game_by_title(game_title)
        if not game:
            logger.error(f"Game '{game_title}' not found on server")
            return False

        game_id = game['id']
        iframe_url = game.get('iframe_url', '')

        # Проверяем, есть ли URL для захвата скриншота
        if not iframe_url or game['img_or_link'] != 'link':
            logger.error(f"Game '{game_title}' is not a link-type game or has no iframe_url")
            return False

        # Захватываем новый скриншот
        screenshot_path = self.capture_screenshot(iframe_url)
        if not screenshot_path:
            logger.error(f"Failed to capture screenshot for '{game_title}'")
            return False

        # Заменяем изображение
        success = self.replace_game_image(game_id, screenshot_path)
        if success:
            # Закомментировано удаление файла для сохранения скриншотов локально
            # try:
            #     os.remove(screenshot_path)
            #     logger.info(f"Cleaned up screenshot file: {screenshot_path}")
            # except Exception as e:
            #     logger.warning(f"Failed to remove screenshot file: {e}")
            logger.info(f"Screenshot retained at: {screenshot_path}")
        return success

def main():
    if len(sys.argv) != 2:
        logger.error("Usage: python replace_game_image.py <game_title>")
        print("Usage: python replace_game_image.py <game_title>")
        sys.exit(1)

    game_title = sys.argv[1]
    logger.info(f"Starting image replacement for game: {game_title}")

    replacer = GameImageReplacer()
    
    if not replacer.login():
        logger.error("Failed to authenticate. Check credentials in .env")
        sys.exit(1)

    if not replacer.load_all_games():
        logger.error("Failed to load games from server")
        sys.exit(1)

    success = replacer.process_game(game_title)
    if success:
        logger.info(f"Successfully updated image for '{game_title}'")
        print(f"Image for '{game_title}' updated successfully")
    else:
        logger.error(f"Failed to update image for '{game_title}'")
        print(f"Failed to update image for '{game_title}'")
        sys.exit(1)

if __name__ == "__main__":
    main()