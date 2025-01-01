import google.generativeai as genai
import PIL.Image
import sys
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    sys.exit(1)
    
genai.configure(api_key=gemini_api_key)

def analyze_visual_style(image_path):
    # Check if file is too small (likely blank screenshot)
    file_size = os.path.getsize(image_path)
    if file_size < 5120:  # 5KB
        error_msg = f"[{datetime.datetime.now()}] Error: Blank screenshot detected - {image_path}\n"
        with open("log.txt", "a") as log_file:
            log_file.write(error_msg)
        return ""

    try:
        image = PIL.Image.open(image_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)

    # Initialize model
    model = genai.GenerativeModel("gemini-1.5-flash-8b")

    # Define prompt
    prompt = """
Create a short sentence visual style description. Follow these exact examples:

Examples:
"Neon-lit anime aesthetics with blue-pink palette. Dark atmospheric backgrounds with vibrant glow effects. "
"Scaly scarlet background, as if made of dragon scales. Card embellishment with gold ornamentation in antique style. Gold text. The feeling of the overwhelming power of the dragons. "

"Yellow sandy background reminiscent of the desert. Oriental motifs."
"Bright cute style, lush greens and sunny tones in the background. Luxury."
"Dark red, burgundy background. Light colored cards with text, anime style images. "

Rules: 
- NO specific characters or scenes
- NO story elements
- Completely ignore the content of the text. 
- Focus ONLY on:
  * Color scheme
  * Art style
  * Interface design
  * Overall impact
"""

    # Generate response
    response = model.generate_content([prompt, image])
    return response.text

if __name__ == "__main__":
    # Get image path from command line
    if len(sys.argv) != 2:
        print("Usage: python vision_query.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    description = analyze_visual_style(image_path)
    print(description)
