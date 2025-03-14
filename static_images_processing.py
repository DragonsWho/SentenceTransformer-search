# static_images_processing.py

import os
import shutil
import logging
from pathlib import Path
import subprocess
from PIL import Image
import sys
import math

logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging for standalone testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger()

def check_cwebp():
    """Check if cwebp is installed"""
    try:
        result = subprocess.run(["cwebp", "-version"], 
                                capture_output=True, 
                                text=True, 
                                check=False)
        return result.returncode == 0
    except FileNotFoundError:
        logger.warning("cwebp command not found. Will use PIL for WebP conversion which might be slower")
        return False

def convert_to_webp(image_path, output_path, lossless=True, quality=90):
    """Convert an image to WebP format using either cwebp or PIL"""
    cwebp_available = check_cwebp()
    
    if cwebp_available:
        # Use cwebp command-line tool for conversion
        lossless_flag = "-lossless" if lossless else ""
        command = ["cwebp", lossless_flag, "-mt", "-q", str(quality), str(image_path), "-o", str(output_path)]
        
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                logger.error(f"cwebp conversion failed: {result.stderr}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error using cwebp: {str(e)}")
            return False
    else:
        # Fallback to PIL/Pillow
        try:
            with Image.open(image_path) as img:
                if img.mode == 'RGBA':
                    # Keep transparency
                    img.save(output_path, 'WEBP', lossless=lossless, quality=quality)
                else:
                    # Convert to RGB first if needed
                    img = img.convert('RGB')
                    img.save(output_path, 'WEBP', lossless=lossless, quality=quality)
            return True
        except Exception as e:
            logger.error(f"Error converting with PIL: {str(e)}")
            return False

def create_cropped_screenshots(folder_path, images=None):
    """
    Create screenshots for the game:
    - screenshots/screenshot.webp: 960×1280 with quality 75 (cropped to top part)
    - screenshots/screenshot_preview.webp: 480×640 with quality 10 (cropped to top part)
    - preview/page1.webp: height = 2*width, quality 10 (preserving original width)
    """
    folder_path = Path(folder_path)
    screenshots_dir = folder_path / "screenshots"
    preview_dir = folder_path / "preview"  # Now at the same level as screenshots folder
    
    os.makedirs(screenshots_dir, exist_ok=True)
    os.makedirs(preview_dir, exist_ok=True)
    
    screenshot_path = screenshots_dir / "screenshot.webp"
    screenshot_preview_path = screenshots_dir / "screenshot_preview.webp"
    preview_path = preview_dir / "preview.webp"
    
    # If no images provided, find them
    if not images:
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.svg')
        images = sorted([
            f for f in folder_path.iterdir() 
            if f.suffix.lower() in image_extensions and f.is_file()
        ])
    
    if not images:
        logger.error(f"No images found in folder: {folder_path}")
        return False
    
    # Use the first image to create screenshots
    try:
        source_image = images[0]
        logger.info(f"Creating screenshots from first image: {source_image}")
        
        # Open image with PIL
        with Image.open(source_image) as img:
            original_width, original_height = img.size
            
            # 1. Create screenshot.webp (960×1280)
            target_width, target_height = 960, 1280
            
            # Create a copy to work with
            resized_img = img.copy()
            
            # Resize maintaining aspect ratio to match target width
            if original_width != target_width:
                resize_ratio = target_width / original_width
                new_height = int(original_height * resize_ratio)
                resized_img = resized_img.resize((target_width, new_height), Image.LANCZOS)
                resized_width, resized_height = resized_img.size
            else:
                resized_width, resized_height = original_width, original_height
            
            # Crop to target height (top part) if necessary
            if resized_height > target_height:
                cropped_img = resized_img.crop((0, 0, resized_width, target_height))
            else:
                # If image is too short, create a white (or transparent) canvas
                cropped_img = Image.new(resized_img.mode, (target_width, target_height), (255, 255, 255))
                cropped_img.paste(resized_img, (0, 0))
            
            # Save as WebP with quality 75
            cropped_img.save(screenshot_path, 'WEBP', quality=75)
            logger.info(f"Saved screenshot to {screenshot_path}")
            
            # 2. Create screenshot_preview.webp (480×640, quality 10)
            preview_img = cropped_img.resize((480, 640), Image.LANCZOS)
            preview_img.save(screenshot_preview_path, 'WEBP', quality=10)
            logger.info(f"Saved preview screenshot to {screenshot_preview_path}")
            
        # 3. Create preview/page1.webp (height = 2*width, quality 10)
        with Image.open(source_image) as orig_img:
            orig_width, orig_height = orig_img.size
            # Calculate new height as twice the width (1:2 ratio)
            preview_height = orig_width * 2
            
            # Create new image with desired aspect ratio
            if orig_height > preview_height:
                # If original is taller than needed, crop top part
                page_preview = orig_img.crop((0, 0, orig_width, preview_height))
            else:
                # If original is shorter, create white canvas and paste original at top
                page_preview = Image.new(orig_img.mode, (orig_width, preview_height), (255, 255, 255))
                page_preview.paste(orig_img, (0, 0))
            
            # Save with quality 10
            page_preview.save(preview_path, 'WEBP', quality=10)
            logger.info(f"Saved page preview to {preview_path}")
            
        return True
    except Exception as e:
        logger.error(f"Error creating screenshots: {str(e)}")
        return False

def process_images_in_folder(folder_path):
    """
    Process all images in a folder:
    1. Convert all images to lossless WebP
    2. Move original images to 'old' subfolder
    3. Create screenshots as required
    """
    logger.info(f"Processing images in folder: {folder_path}")
    folder_path = Path(folder_path)
    
    if not folder_path.exists() or not folder_path.is_dir():
        logger.error(f"Folder does not exist or is not a directory: {folder_path}")
        return False
    
    # Create 'old' subfolder for originals
    old_dir = folder_path / "old"
    os.makedirs(old_dir, exist_ok=True)
    
    # Find all images in the folder
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.svg')
    images = [
        f for f in folder_path.iterdir() 
        if f.suffix.lower() in image_extensions and f.is_file()
    ]
    
    if not images:
        logger.warning(f"No images found in folder: {folder_path}")
        return False
    
    # Sort images by name for consistent processing
    images = sorted(images)
    
    # Process each image
    successfully_processed = []
    for image_path in images:
        # Skip if it's already a WebP file to avoid unnecessary processing
        if image_path.suffix.lower() == '.webp':
            logger.info(f"Image already in WebP format: {image_path}")
            successfully_processed.append(image_path)
            continue
        
        # Prepare output path (same name but .webp extension)
        webp_path = folder_path / f"{image_path.stem}.webp"
        
        # Convert to WebP
        logger.info(f"Converting {image_path} to WebP")
        if convert_to_webp(image_path, webp_path, lossless=True):
            # Move original to 'old' folder
            try:
                shutil.move(image_path, old_dir / image_path.name)
                logger.info(f"Moved original to: {old_dir / image_path.name}")
                successfully_processed.append(webp_path)
            except Exception as e:
                logger.error(f"Error moving original image: {str(e)}")
        else:
            logger.error(f"Failed to convert: {image_path}")
    
    # Use actual WebP files for creating screenshots
    webp_images = [
        f for f in folder_path.iterdir()
        if f.suffix.lower() == '.webp' and f.is_file()
    ]
    
    # Create screenshots
    if webp_images:
        create_cropped_screenshots(folder_path, sorted(webp_images))
    else:
        logger.warning("No WebP images found to create screenshots from")
    
    logger.info(f"Processed {len(successfully_processed)}/{len(images)} images in {folder_path}")
    return len(successfully_processed) > 0

def main():
    """Main function for standalone testing"""
    logger = setup_logging()
    
    if len(sys.argv) < 2:
        logger.error("Usage: python static_images_processing.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    logger.info(f"Processing folder: {folder_path}")
    
    success = process_images_in_folder(folder_path)
    if success:
        logger.info("Image processing completed successfully")
    else:
        logger.error("Image processing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()