todo


-------настроить прокрутку
- настроить комментарии к тегам и их обрезку
- проверка имен авторов
- проверка наличия игры в базе
- длинные дефисы
- возможно настройка более веселых описаний для каталога
- скрины по кнопке, что бы разворачивать описания
- убрать паузу
- брлять, теги дублируются
- pause for screenshots
- добавление скриншотов гроку, авось приложатся. А нет, так нет.


OCR для статики
промпт замени, нече ссылку указывать



поменять промпт для поисковичка, преедавать ему автора, название т.д.


отображение лайкнутых игр в профиле

добавить ссылку для открытия в новом окошке

размер игры 
дата первой публикации



branching/open-ended и т.д.
подсказки для тэгов слишком быстрые

sfw тэг




скрин на стоп не реагирует
лишние проверки уже скачанных файлов при извлечении json
поменять поиск json в js

удалялка незагруженной картинки в апи грок


доюавить рамочку красной кнопки "во весь экран" а то иногда сливается


внесение в базу и поиск
серверный поиск

уточняющие вопросы от очень простой модельки?

близкие по координатам игры в рекомендации, можно выбрать несколько



















# Using ChromaDB for CYOA Game Search

to use BAAI/bge-m3 add -M3 flag

## 1. How to Use New Functions in vector_search

### Basic Setup
```bash
# Install required packages
pip install chromadb openai python-dotenv

# Make sure you have DeepInfra API key in .env file
# DEEPINFRA_API_KEY=your_api_key_here
```

### Initialize Database
```bash
# Process all markdown files in summaries/ directory and create vector database
python vector_search.py --init
```

### Update Database with a New Game
```bash
# Add or update a single game file
python vector_search.py --update path/to/game_summary.md https://game-url.com
```

### Search for Similar Games
```bash
# Search for games matching your description
python vector_search.py --search "cyberpunk game with implants and rebellion"

# For more complex queries with quotes, use single quotes outside
python vector_search.py --search 'game about "mind control" in a fantasy setting'
```

### Example Search Output
```
Search Results:

1. Cyber Dystopia CYOA (Similarity: 0.87)
   URL: https://example.com/cyber_dystopia
   Preview: In this cyberpunk adventure, you navigate a world dominated by mega-corporations. Choose your implants wisely as they determine your abilities in the coming rebellion...

2. Neo Tokyo 2050 (Similarity: 0.75)
   URL: https://example.com/neo_tokyo
   Preview: A futuristic CYOA where you can augment your body with various cybernetic enhancements. The story follows the underground resistance...
``` 