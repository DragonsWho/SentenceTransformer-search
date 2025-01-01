import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

def capture_network_traffic(url):
    # Configure Chrome to capture network traffic
    capabilities = DesiredCapabilities.CHROME
    capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
    
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    # Initialize WebDriver with logging preferences
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    driver = webdriver.Chrome(service=Service(), options=options)
    
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Get network logs
        logs = driver.get_log('performance')
        
        # Process network logs to find data requests
        data_requests = []
        for log in logs:
            try:
                message = json.loads(log['message'])
                params = message['message']['params']
                request = params['request']
                
                # Filter for JSON/JavaScript requests
                if 'url' in request and any(ext in request['url'] for ext in ['.json', '.js']):
                    data_requests.append({
                        'url': request['url'],
                        'method': request['method'],
                        'type': params.get('type', 'unknown')
                    })
            except (KeyError, json.JSONDecodeError):
                continue
        
        print(f"\nFound {len(data_requests)} potential data requests:")
        
        # Print details of data requests
        for i, req in enumerate(data_requests):
            print(f"\nRequest {i+1}:")
            print(f"URL: {req['url']}")
            print(f"Method: {req['method']}")
            print(f"Type: {req['type']}")
            
    finally:
        driver.quit()

if __name__ == "__main__":
    url = "https://dragonswhore-cyoas.neocities.org/Fucking_Hentai_Nightmare/"
    capture_network_traffic(url)
