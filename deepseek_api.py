import os
from dotenv import load_dotenv
import requests
 
load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def call_deepseek_chat(system_message: str, user_message: str) -> dict:
    """
    Calls the DeepSeek Chat API with the given messages
    
    Args:
        system_message (str): System message
        user_message (str): User request
    
    Returns:
        dict: API Response
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }
    
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()

if __name__ == "__main__": 
    system_msg = "You are a helpful assistant."
    user_msg = "Hello!"
    
    try:
        result = call_deepseek_chat(system_msg, user_msg)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
