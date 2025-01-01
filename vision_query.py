import google.generativeai as genai
import PIL.Image

# Configure API key
genai.configure(api_key="AIzaSyDJyDrjC8IvCkEKDotXkzGmVS46cNKc7y8")

# Load image
image = PIL.Image.open("screenshoots/Arabian_nights.png")

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

# Print result
print(response.text)
