from PIL import Image
import os
import shutil
import sys

def convert_to_lossless_webp(input_path, output_path=None):
    """Конвертирует изображение в lossless WebP с проверкой максимального размера"""
    try:
        with Image.open(input_path) as img:
            width, height = img.size
            MAX_WEBP_SIZE = 16383  # Максимальный размер WebP в пикселях
            if width > MAX_WEBP_SIZE or height > MAX_WEBP_SIZE:
                return "size_exceeded"
            if output_path is None:
                output_path = os.path.splitext(input_path)[0] + '.webp'
            img.save(output_path, 'WEBP', lossless=True, quality=100)
            print(f"Успешно сконвертировано: {output_path}")
        return True
    except Exception as e:
        print(f"Ошибка при конвертации {input_path}: {str(e)}")
        return "general_error"

def create_game_screenshot(input_folder, output_folder=None):
    """Создаёт скриншот верхней части первой картинки в стиле Puppeteer и сохраняет в screenshots/screenshot.webp"""
    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
    
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(supported_extensions)]
    if not files:
        print(f"В папке {input_folder} нет поддерживаемых изображений")
        return
    
    first_file = sorted(files)[0]
    input_path = os.path.join(input_folder, first_file)
    
    with Image.open(input_path) as img:
        width, height = img.size
        MAX_WEBP_SIZE = 16383
        if width > MAX_WEBP_SIZE or height > MAX_WEBP_SIZE:
            game_name = os.path.basename(input_folder)
            error_message = f"""
===========================
Изображение {first_file} имеет слишком большую длину и его требуется рассечь!
Игра {game_name} не обработана!
===========================
"""
            print(error_message)
            sys.exit(1)
    
    output_dir = output_folder or input_folder
    screenshot_folder = os.path.join(output_dir, 'screenshots')
    os.makedirs(screenshot_folder, exist_ok=True)
    
    with Image.open(input_path) as img:
        width, height = img.size
        target_width = 1920
        target_height = 2560
        aspect_ratio = target_width / target_height
        
        crop_height = min(height, int(width / aspect_ratio))
        crop_box = (0, 0, width, crop_height)
        
        cropped_img = img.crop(crop_box)
        resized_img = cropped_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        output_path = os.path.join(screenshot_folder, 'screenshot.webp')
        resized_img.save(output_path, 'WEBP', quality=80)
        print(f"Скриншот сохранён: {output_path}")

def convert_folder_to_webp(input_folder, output_folder=None):
    """Конвертирует все изображения в WebP, перемещает оригиналы в /old_pictures и создаёт скриншот"""
    supported_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    
    if output_folder is None:
        output_folder = input_folder
    
    old_pictures_folder = os.path.join(input_folder, 'old_pictures')
    os.makedirs(old_pictures_folder, exist_ok=True)
    
    # Конвертируем файлы
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(supported_extensions):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, os.path.splitext(filename)[0] + '.webp')
            result = convert_to_lossless_webp(input_path, output_path)
            if result is not True:
                game_name = os.path.basename(input_folder)
                if result == "size_exceeded":
                    error_message = f"""
===========================
Изображение {filename} имеет слишком большую длину и его требуется рассечь!
Игра {game_name} не обработана!
===========================
"""
                else:  # general_error
                    error_message = f"""
===========================
Ошибка обработки изображения {filename}!
Игра {game_name} не обработана из-за проблем с конвертацией!
===========================
"""
                print(error_message)
                sys.exit(1)
            old_path = os.path.join(old_pictures_folder, filename)
            shutil.move(input_path, old_path)
            print(f"Оригинал перемещён в: {old_path}")
    
    create_game_screenshot(input_folder, output_folder)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        convert_folder_to_webp(input_dir, output_dir)
    else:
        print("Укажите путь к папке как аргумент. Пример: python img_to_webp.py cyoa_static/alchemical_potions")