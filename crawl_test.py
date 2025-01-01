import requests
import json

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

def try_alternative_urls(base_url):
    """Try different possible data file locations"""
    possible_paths = [
        '/project.json',
        '/data.json',
        '/game.json',
        '/content.json',
        '/story.json'
    ]
    
    for path in possible_paths:
        url = base_url + path
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return url, response.json()
        except:
            continue
    
    return None, None

def process_url(url):
    """Process single URL with support for alternative data locations"""
    try:
        # Try the original URL first
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
        else:
            # Try alternative data locations
            base_url = url.replace('/project.json', '')
            url, data = try_alternative_urls(base_url)
            if data is None:
                print(f"No valid data found for {base_url}")
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
        print("Usage: python crawl_test.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    process_url(url)

if __name__ == "__main__":
    main()
