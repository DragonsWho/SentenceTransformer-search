import requests
import json

def json_to_md(data):
    """Convert JSON data to Markdown format"""
    md_content = []
    
    # Extract main content
    if 'rows' in data:
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
                    # Skip image links
                    pass
    
    return "\n".join(md_content)

def process_url(url):
    """Process single URL: download JSON and convert to Markdown"""
    try:
        # Fetch JSON data
        response = requests.get(url)
        data = response.json()
        
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
        
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        return None

def main():
    # Read URLs from file
    with open('links.txt', 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    # Process each URL
    for url in urls:
        process_url(url)

if __name__ == "__main__":
    main()
