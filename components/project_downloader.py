# components/project_downloader.py

import os
import re
import json
import logging
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from bs4 import BeautifulSoup
from functools import lru_cache
from pathlib import Path
from email.utils import formatdate
from time import time
import chardet
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
from pathlib import Path
import requests
import logging

# Set up logging
log_file_path = os.path.join('logs', 'project_downloader.log')
logging.basicConfig(
    filename=log_file_path,
    level=logging.DEBUG,  # Установим DEBUG для более детального анализа
    format='%(asctime)s - %(levelname)s - %(message)s'
)

metadata_lock = threading.Lock()

# -------------------- Helper Functions -------------------- #

def detect_encoding(content):
    logging.debug("Detecting encoding for content.")
    result = chardet.detect(content)
    return result['encoding'] if result['encoding'] else 'utf-8'

@lru_cache(maxsize=1000)
def is_valid_url(url, base_domain):
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    if parsed.scheme not in {'http', 'https'}:
        return False
    if parsed.netloc != base_domain:
        return False
    if re.search(r'[()<>{}\s\\]', parsed.path):
        return False
    return True

def extract_urls_from_css(css_content):
    urls = re.findall(r'url\((?:\'|"|)(.*?)(?:\'|"|)\)', css_content)
    return urls

def is_local_resource(src, base_url):
    if src.startswith('http://') or src.startswith('https://'):
        return urlparse(src).netloc == urlparse(base_url).netloc
    if src.startswith('//'):
        return urlparse(base_url).netloc == src.split('/')[2]
    return True

def sanitize_folder_name(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def get_game_name(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    path = parsed_url.path.strip('/')
    if not path:
        return domain, ''
    path_parts = path.split('/')
    game_name = path_parts[-1] if path_parts else ''
    return domain, game_name

def enumerate_project_resources(data, directories=['images', 'music', 'videos', 'fonts', 'css', 'js', 'audio', 'assets']):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                for directory in directories:
                    if value.startswith(f"{directory}/"):
                        yield value
            elif isinstance(value, (dict, list)):
                yield from enumerate_project_resources(value, directories)
    elif isinstance(data, list):
        for item in data:
            yield from enumerate_project_resources(item, directories)

# -------------------- Downloading Function -------------------- #

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=100,
        pool_maxsize=100,
        pool_block=False
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    })
    return session

def download_file(url, path, session, base_domain, metadata_path, retries=3, delay=5, request_delay=0.1):
    """
    Скачивает файл и обновляет метаданные, полагаясь только на ETag для проверки актуальности.
    
    Args:
        url (str): URL файла для загрузки
        path (str): Локальный путь для сохранения файла
        session (requests.Session): Сессия для HTTP-запросов
        base_domain (str): Базовый домен для проверки валидности URL
        metadata_path (str): Путь к файлу метаданных (metadata.json)
        retries (int): Количество попыток повторного запроса
        delay (int): Задержка между повторными попытками
        request_delay (float): Задержка после успешной загрузки
    
    Returns:
        tuple: (success: bool, was_downloaded: bool)
    """
    path = Path(path)
    metadata_path = Path(metadata_path)

    # Пропускаем специальные случаи
    if url.endswith('favicon.ico') or url.startswith('data:'):
        logging.debug(f"Skipping special URL: {url}")
        return True, False

    # Читаем существующие метаданные
    metadata = {}
    if metadata_path.exists():
        try:
            with metadata_path.open('r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logging.warning(f"Could not load metadata from {metadata_path}: {e}")

    # Проверка актуальности по ETag
    if path.exists() and url in metadata:
        local_metadata = metadata.get(url, {})
        local_etag = local_metadata.get('ETag')
        logging.debug(f"Checking file: {url}, Local ETag: {local_etag}, File exists: {path.exists()}")

        if local_etag:
            try:
                headers = {'If-None-Match': local_etag}
                head = session.head(url, allow_redirects=True, timeout=15, headers=headers)
                head.raise_for_status()

                if head.status_code == 304:
                    logging.debug(f"File up to date (304 Not Modified): {path}")
                    return True, False

                server_etag = head.headers.get('ETag')
                if server_etag == local_etag:
                    logging.debug(f"File matches by ETag: {path}")
                    return True, False
            except requests.RequestException as e:
                logging.warning(f"HEAD request failed for {url}: {e}, proceeding to download")

    # Скачивание файла
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with session.get(url, stream=True, timeout=15) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            server_etag = response.headers.get('ETag')

            is_text_file = (
                path.suffix.lower() in {'.html', '.htm', '.js', '.css', '.json', '.txt', '.xml', '.svg'} or
                'text' in content_type or 'javascript' in content_type
            )
            if is_text_file:
                content = response.content
                encoding = detect_encoding(content)
                text = content.decode(encoding, errors='replace')
                path.write_text(text, encoding='utf-8')
            else:
                with path.open('wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            # Обновляем метаданные с синхронизацией
            with metadata_lock:
                if metadata_path.exists():
                    try:
                        with metadata_path.open('r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except Exception:
                        logging.warning(f"Reloading metadata failed, using empty dict: {metadata_path}")
                        metadata = {}
                metadata[url] = {'ETag': server_etag}
                metadata_path.parent.mkdir(parents=True, exist_ok=True)
                with metadata_path.open('w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)

            logging.debug(f"Downloaded and updated metadata: {url} -> {path}, Server ETag: {server_etag}")
            sleep(request_delay)
            return True, True
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return False, False

def parse_html_for_resources(html_content, base_url, base_domain):
    soup = BeautifulSoup(html_content, 'html.parser')
    resources = set()
    parsed_base = urlparse(base_url)
    if not base_url.endswith('/'):
        base_url += '/'

    tags = soup.find_all(['link', 'script', 'img', 'video', 'audio', 'source'])
    logging.debug(f"Found {len(tags)} tags with potential resources")

    for tag in tags:
        src = tag.get('href') or tag.get('src')
        if src:
            logging.debug(f"Processing resource: {src} from tag: {tag.name}")
            src = src.replace('\\', '/').strip()
            if is_local_resource(src, base_url):
                if not src.startswith('data:'):
                    if src.startswith('/'):
                        full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{src}"
                    else:
                        full_url = urljoin(base_url, src)
                    if is_valid_url(full_url, base_domain):
                        logging.debug(f"Adding resource: {full_url}")
                        resources.add(full_url)

    for style_tag in soup.find_all('style'):
        css_content = style_tag.string
        if css_content:
            urls = extract_urls_from_css(css_content)
            for url in urls:
                url = url.replace('\\', '/').strip()
                if url.startswith('/'):
                    full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
                else:
                    full_url = urljoin(base_url, url)
                if is_valid_url(full_url, base_domain):
                    resources.add(full_url)

    for tag in soup.find_all(style=True):
        style_content = tag['style']
        urls = extract_urls_from_css(style_content)
        for url in urls:
            url = url.replace('\\', '/').strip()
            if url.startswith('/'):
                full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{url}"
            else:
                full_url = urljoin(base_url, url)
            if is_valid_url(full_url, base_domain):
                resources.add(full_url)

    embedded_scripts = soup.find_all('script')
    for script in embedded_scripts:
        if script.string:
            js_urls = re.findall(r"""['"]([^'"]+?\.js(?:\?.*)?)['"]""", script.string)
            for js_url in js_urls:
                js_url = js_url.replace('\\', '/').strip()
                if is_local_resource(js_url, base_url):
                    if js_url.startswith('/'):
                        full_js_url = f"{parsed_base.scheme}://{parsed_base.netloc}{js_url}"
                    else:
                        full_js_url = urljoin(base_url, js_url)
                    if is_valid_url(full_js_url, base_domain):
                        resources.add(full_js_url)

    logging.debug(f"Total resources found: {len(resources)}")
    return resources

def parse_css_for_resources(css_content, base_url, base_domain):
    resources = set()
    urls = extract_urls_from_css(css_content)
    for url in urls:
        url = url.replace('\\', '/').strip()
        full_url = urljoin(base_url, url)
        if is_valid_url(full_url, base_domain):
            resources.add(full_url)
    return resources

def handle_resource(full_url, session, base_path, base_url_path, base_domain, metadata_path):
    logging.debug(f"Starting to handle resource: {full_url}")
    parsed_url = urlparse(full_url)
    path = parsed_url.path.lstrip('/')
    base_url_path_clean = base_url_path.lstrip('/').rstrip('/')
    if path.startswith(base_url_path_clean):
        relative_path = path[len(base_url_path_clean):].lstrip('/')
    else:
        relative_path = path
    file_path = os.path.join(base_path, relative_path)
    logging.debug(f"Saving resource to: '{file_path}'")
    if not is_valid_url(full_url, base_domain):
        logging.warning(f"Invalid or external URL skipped: {full_url}")
        return False
    success, was_downloaded = download_file(full_url, file_path, session, base_domain, metadata_path)
    if not success:
        logging.error(f"Failed to download resource: {full_url}")
        return False
    if file_path.endswith('.css'):
        try:
            with open(file_path, 'r', encoding='utf-8') as css_file:
                css_content = css_file.read()
            css_resources = parse_css_for_resources(css_content, full_url, base_domain)
            logging.debug(f"Found {len(css_resources)} resources in CSS: {file_path}")
            for css_res in css_resources:
                handle_resource(css_res, session, base_path, base_url_path, base_domain, metadata_path)
        except Exception as e:
            logging.error(f"Error parsing CSS {file_path}: {e}")
    return success

def crawl_and_download(url, base_path, session=None, max_workers=5):
    if session is None:
        session = create_session()
    
    base_path = Path(base_path)
    metadata_path = base_path / 'metadata.json'

    # Загрузка index.html
    index_path = base_path / 'index.html'
    index_success, index_downloaded = download_file(
        url, index_path, session, urlparse(url).netloc, metadata_path
    )
    if not index_success:
        logging.error(f"Failed to download index.html for {url}")
        return 0, 0, 0

    raw_content = index_path.read_bytes() if index_path.exists() else b""
    encoding = detect_encoding(raw_content)
    try:
        html_content = raw_content.decode(encoding, errors='replace')
    except Exception as e:
        logging.error(f"Error decoding content from {url}: {e}")
        html_content = ""

    parsed_base = urlparse(url)
    base_domain = parsed_base.netloc
    base_url_path = parsed_base.path
    if not base_url_path.endswith('/'):
        base_url_path += '/'

    resources = parse_html_for_resources(
        html_content, 
        f"{parsed_base.scheme}://{parsed_base.netloc}{parsed_base.path}", 
        base_domain
    )

    project_json_url = urljoin(f"{parsed_base.scheme}://{base_domain}{base_url_path}", 'project.json')
    project_json_path = base_path / 'project.json'
    project_json_success, project_json_downloaded = download_file(
        project_json_url, 
        project_json_path, 
        session, 
        base_domain,
        metadata_path,
        retries=3,
        delay=1
    )

    if project_json_success and project_json_downloaded:
        logging.debug(f"Successfully downloaded project.json from {project_json_url}")
        try:
            project_data = json.loads(project_json_path.read_text(encoding='utf-8'))
            project_resources = enumerate_project_resources(project_data)
            for res in project_resources:
                full_res_url = urljoin(f"{parsed_base.scheme}://{base_domain}{base_url_path}", res)
                if is_valid_url(full_res_url, base_domain):
                    resources.add(full_res_url)
                    logging.debug(f"Added resource from project.json: {full_res_url}")
        except json.JSONDecodeError:
            logging.error(f"Error decoding project.json from {project_json_url}")
        except Exception as e:
            logging.error(f"Unexpected error processing project.json from {project_json_url}: {e}")
    else:
        logging.warning(f"Failed to download project.json from {project_json_url}")

    logging.debug(f"Starting download of {len(resources)} resources")
    completed = 1 if index_success else 0
    downloaded = 1 if index_downloaded else 0
    failed = 0 if index_success else 1
    if project_json_success and project_json_downloaded:
        downloaded += 1
    elif not project_json_success:
        failed += 1
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_resource = {
            executor.submit(
                handle_resource, 
                res, 
                session, 
                base_path, 
                base_url_path, 
                base_domain,
                metadata_path
            ): res for res in resources
        }

        for future in as_completed(future_to_resource):
            res = future_to_resource[future]
            try:
                success = future.result()
                if success:
                    completed += 1
                    # Проверяем, был ли файл загружен (временное решение через размер)
                    file_path = os.path.join(base_path, urlparse(res).path.lstrip('/'))
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        downloaded += 1
                else:
                    failed += 1
                logging.debug(f"Resource {res} processing completed. Success: {success}")
            except Exception as e:
                failed += 1
                logging.error(f"Error processing resource {res}: {e}")

    logging.info(f"Download completed. Successfully processed: {completed}, Actually downloaded: {downloaded}, Failed: {failed}")
    return completed, downloaded, failed

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python project_downloader.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    base_path = f"downloaded_games/{url.split('/')[-2]}"
    completed, downloaded, failed = crawl_and_download(url, base_path)
    print(f"Completed: {completed}, Downloaded: {downloaded}, Failed: {failed}")