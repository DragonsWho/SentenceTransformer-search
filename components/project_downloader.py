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

# Set up logging
log_file_path = os.path.join('logs', 'project_downloader.log')
logging.basicConfig(
    filename=log_file_path,
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    path = Path(path)
    metadata_path = Path(metadata_path)  # Путь к metadata.json в папке проекта

    # Пропускаем специальные случаи
    if url.endswith('favicon.ico') or url.startswith('data:'):
        logging.debug(f"Skipping special URL: {url}")
        return True

    # Читаем существующие метаданные
    metadata = {}
    if metadata_path.exists():
        try:
            with metadata_path.open('r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logging.warning(f"Could not load metadata from {metadata_path}: {e}")

    # Проверка актуальности файла
    if path.exists() and url in metadata:
        try:
            local_metadata = metadata.get(url, {})
            local_etag = local_metadata.get('ETag')
            local_mtime = local_metadata.get('Last-Modified')
            local_size = local_metadata.get('Content-Length', 0)

            # Запрос HEAD с If-None-Match для ETag
            headers = {}
            if local_etag:
                headers['If-None-Match'] = local_etag
            elif local_mtime:
                headers['If-Modified-Since'] = local_mtime

            head = session.head(url, allow_redirects=True, timeout=15, headers=headers)
            head.raise_for_status()

            if head.status_code == 304:
                logging.debug(f"File up to date (304 Not Modified): {path}")
                return True

            server_etag = head.headers.get('ETag')
            server_mtime = head.headers.get('Last-Modified')
            server_size = int(head.headers.get('Content-Length', 0))

            # Если ETag совпадает, файл актуален
            if server_etag and server_etag == local_etag:
                logging.debug(f"File matches by ETag: {path}")
                return True
            # Проверка по Last-Modified и размеру
            elif server_mtime and server_mtime == local_mtime and server_size == local_size:
                logging.debug(f"File matches by Last-Modified and size: {path}")
                return True
            # Только размер как запасной вариант
            elif server_size == local_size and server_size != 0:
                logging.debug(f"File matches by size: {path}")
                return True
        except Exception as e:
            logging.warning(f"Could not verify file metadata for {url}: {e}")

    # Скачивание файла
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with session.get(url, stream=True, timeout=15) as response:
            response.raise_for_status()
            content_type = response.headers.get('Content-Type', '')
            server_etag = response.headers.get('ETag')
            server_mtime = response.headers.get('Last-Modified')
            server_size = int(response.headers.get('Content-Length', 0))

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

            # Обновляем метаданные
            metadata[url] = {
                'ETag': server_etag,
                'Last-Modified': server_mtime,
                'Content-Length': server_size
            }
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with metadata_path.open('w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            logging.debug(f"Downloaded and updated metadata: {url} -> {path}")
            sleep(request_delay)
            return True
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return False

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
    success = download_file(full_url, file_path, session, base_domain, metadata_path)
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
    return True

def crawl_and_download(url, base_path, session=None, max_workers=5):
    if session is None:
        session = create_session()
    
    base_path = Path(base_path)
    metadata_path = base_path / 'metadata.json'

    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error downloading page {url}: {e}")
        return 0, 0

    raw_content = response.content
    encoding = detect_encoding(raw_content)
    try:
        html_content = raw_content.decode(encoding, errors='replace')
    except Exception as e:
        logging.error(f"Error decoding content from {url}: {e}")
        html_content = raw_content.decode('utf-8', errors='replace')

    index_path = base_path / 'index.html'
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(html_content, encoding='utf-8')
        logging.debug(f"Saved index.html: {index_path}")
    except Exception as e:
        logging.error(f"Error saving index.html to {index_path}: {e}")

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
    project_json_downloaded = download_file(
        project_json_url, 
        project_json_path, 
        session, 
        base_domain,
        metadata_path,
        retries=3,
        delay=1
    )

    if project_json_downloaded:
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
    completed = 0
    failed = 0
    
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
                result = future.result()
                if result:
                    completed += 1
                else:
                    failed += 1
                logging.debug(f"Resource {res} download completed. Success: {result}")
            except Exception as e:
                failed += 1
                logging.error(f"Error processing resource {res}: {e}")

    logging.info(f"Download completed. Successfully downloaded: {completed}, Failed: {failed}")
    return completed, failed

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python project_downloader.py <url>")
        sys.exit(1)
    url = sys.argv[1]
    base_path = f"downloaded_games/{url.split('/')[-2]}"
    completed, failed = crawl_and_download(url, base_path)
    print(f"Completed: {completed}, Failed: {failed}")