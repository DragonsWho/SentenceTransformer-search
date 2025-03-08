import zstandard
import os
import json
import sys
import csv
from datetime import datetime
import logging
import re

# Настройка логирования
log = logging.getLogger("bot")
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

# Путь к входному файлу
input_file = r"path\to\your\file.zst"  # Замените на путь к вашему файлу
# Путь к выходному файлу
output_file = r"path\to\output.csv"    # Замените на путь к выходному файлу

def read_and_decode(reader, chunk_size, max_window_size, previous_chunk=None, bytes_read=0):
    chunk = reader.read(chunk_size)
    bytes_read += chunk_size
    if previous_chunk is not None:
        chunk = previous_chunk + chunk
    try:
        return chunk.decode()
    except UnicodeDecodeError:
        if bytes_read > max_window_size:
            raise UnicodeError(f"Unable to decode frame after reading {bytes_read:,} bytes")
        log.info(f"Decoding error with {bytes_read:,} bytes, reading another chunk")
        return read_and_decode(reader, chunk_size, max_window_size, chunk, bytes_read)

def read_lines_zst(file_name):
    with open(file_name, 'rb') as file_handle:
        buffer = ''
        reader = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(file_handle)
        while True:
            chunk = read_and_decode(reader, 2**27, (2**29) * 2)
            if not chunk:
                break
            lines = (buffer + chunk).split("\n")
            for line in lines[:-1]:
                yield line.strip(), file_handle.tell()
            buffer = lines[-1]
        reader.close()

def extract_links(text):
    # Извлечение всех URL из текста с помощью регулярного выражения
    url_pattern = r'https?://[^\s\[\]()]+'
    return ','.join(re.findall(url_pattern, text)) if text else ''

def process_file(input_file, output_file):
    output_path = output_file
    log.info(f"Input: {input_file} : Output: {output_path}")

    # Открываем CSV-файл для записи
    with open(output_path, 'w', encoding='UTF-8', newline='') as handle:
        writer = csv.writer(handle)
        # Заголовки CSV
        writer.writerow([
            "Date", "Author", "Selftext", "Links", "Removed", "Score", "Flair", "Title"
        ])

        file_size = os.stat(input_file).st_size
        total_lines = 0
        bad_lines = 0

        for line, file_bytes_processed in read_lines_zst(input_file):
            total_lines += 1
            if total_lines % 100000 == 0:
                log.info(f"Processed {total_lines:,} lines : {bad_lines:,} bad : {(file_bytes_processed / file_size) * 100:.0f}%")

            try:
                obj = json.loads(line)
                
                # Извлечение нужных полей
                date = datetime.utcfromtimestamp(int(obj.get('created_utc', 0))).strftime('%Y-%m-%d %H:%M:%S')
                author = obj.get('author', 'N/A')
                selftext = obj.get('selftext', '')
                links = extract_links(selftext)  # Ссылки из текста
                if obj.get('url') and obj.get('url') != f"https://www.reddit.com{obj.get('permalink', '')}":
                    # Добавляем URL, если он не дублирует permalink
                    links = f"{links},{obj['url']}" if links else obj['url']
                removed = 'Yes' if obj.get('_meta', {}).get('removal_type') == 'deleted' else 'No'
                score = obj.get('score', 0)
                flair = obj.get('link_flair_text', '')
                title = obj.get('title', '')

                # Запись строки в CSV
                writer.writerow([date, author, selftext, links, removed, score, flair, title])

            except (KeyError, json.JSONDecodeError) as err:
                bad_lines += 1
                log.warning(f"Error processing line: {err}")

        log.info(f"Complete : {total_lines:,} lines : {bad_lines:,} bad")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    
    process_file(input_file, output_file)