import os
from dotenv import load_dotenv
import requests

# Загружаем переменные из .env файла
load_dotenv()

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def call_deepseek_chat(system_message: str, user_message: str) -> dict:
    """
    Вызывает API DeepSeek Chat с заданными сообщениями
    
    Args:
        system_message (str): Системное сообщение
        user_message (str): Пользовательский запрос
    
    Returns:
        dict: Ответ API
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
    # Пример использования
    system_msg = "You are a helpful assistant."
    user_msg = "Hello!"
    
    try:
        result = call_deepseek_chat(system_msg, user_msg)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
