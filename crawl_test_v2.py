import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def json_to_md(data):
    """Convert JSON data to Markdown format with flexible structure handling"""
    md_content = []
    
    # Handle different JSON structures
    if isinstance(data, dict):
        # Try to extract main content from different possible structures
        if 'rows' in data:
            # Original structure
            for row in data['rows']:
                if 'titleText' in row:
                    md_content.append(f"## {row.get('title', '')}\n")
                    md_content.append(f"{row['titleText']}\n")
                
                if 'objects' in row:
                    for obj in row['objects']:
                        if 'title' in obj:
                            md_content.append(f"### {obj['title']}\n")
                        if 'text' in obj:
                            md_content.append(f"{obj['text']}\n")
        elif 'content' in data:
            # Alternative structure 1
            md_content.append(f"# {data.get('title', 'Untitled')}\n")
            md_content.append(f"{data['content']}\n")
        elif 'sections' in data:
            # Alternative structure 2
            for section in data['sections']:
                md_content.append(f"## {section.get('title', '')}\n")
                md_content.append(f"{section.get('text', '')}\n")
        else:
            # Fallback: try to extract any text content
            for key, value in data.items():
                if isinstance(value, str):
                    md_content.append(f"## {key}\n")
                    md_content.append(f"{value}\n")
    
    return "\n".join(md_content)

def capture_network_traffic(url):
    """Capture network traffic to find JSON files"""
    # Configure Chrome options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    # Enable performance logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # Initialize WebDriver with automatic ChromeDriver management
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Get network logs
        logs = driver.get_log('performance')
        
        # Find all JSON requests
        json_urls = set()
        for log in logs:
            try:
                message = json.loads(log['message'])
                params = message['message']['params']
                request = params['request']
                
                if 'url' in request and request['url'].endswith('.json'):
                    json_urls.add(request['url'])
            except (KeyError, json.JSONDecodeError):
                continue
        
        return list(json_urls)
    finally:
        driver.quit()

def process_url(url):
    """Process single URL by analyzing network traffic"""
    try:
        # Get list of JSON files from network traffic
        json_urls = capture_network_traffic(url)
        
        if not json_urls:
            print(f"No JSON files found for {url}")
            return None
        
        # Try each JSON file until we find valid data
        for json_url in json_urls:
            try:
                response = requests.get(json_url)
                if response.status_code == 200:
                    data = response.json()
                    break
            except:
                continue
        else:
            print(f"No valid data found in JSON files for {url}")
            return None
        
        # Convert to Markdown
        md_content = json_to_md(data)
        
        # Generate filename from URL
        project_name = url.split('/')[-2]
        md_filename = f"markdown/{project_name}.md"
        
        # Extract game title from URL
        game_title = url.split('/')[-2].replace('_', ' ')
        
        # Add title to the beginning of markdown content
        md_content = f"title: {game_title}\n\n{md_content}"
        
        # Save Markdown
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return md_filename
        
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None

def main():
    import sys
    if len(sys.argv) != 2:
        print("Usage: python crawl_test_v2.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    process_url(url)

if __name__ == "__main__":
    main()
