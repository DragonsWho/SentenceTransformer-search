import os
import numpy as np
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

class DeepseekSearchAPI:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
            
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.chat_url = "https://api.deepseek.com/chat/completions"
        self.embeddings_url = "https://api.deepseek.com/embeddings"

    def generate(self, prompt: str, system_message: str = "You are a helpful assistant.") -> str:
        """
        Generate a response using Deepseek Chat API
        
        Args:
            prompt (str): User prompt
            system_message (str): System message to guide the model
            
        Returns:
            str: Generated response
        """
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        
        response = requests.post(self.chat_url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        return response.json()['choices'][0]['message']['content']

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get text embedding using Deepseek Embeddings API
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: Text embedding vector
        """
        payload = {
            "input": text,
            "model": "text-embedding-3-small"
        }
        
        response = requests.post(self.embeddings_url, headers=self.headers, json=payload)
        response.raise_for_status()
        
        return np.array(response.json()['data'][0]['embedding'])

if __name__ == "__main__":
    # Example usage
    api = DeepseekSearchAPI()
    
    # Test chat
    try:
        response = api.generate("Hello!")
        print("Chat Response:", response)
    except Exception as e:
        print(f"Chat Error: {e}")
    
    # Test embeddings
    try:
        embedding = api.get_embedding("Test text")
        print("Embedding Shape:", embedding.shape)
    except Exception as e:
        print(f"Embedding Error: {e}")
