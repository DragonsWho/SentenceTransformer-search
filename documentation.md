## Running the Scripts

### Main Controlling Script
- **controller.py**: This script orchestrates the execution of various functions and scripts in the project. It reads URLs from `links.txt`, processes them through `crawl.py`, and manages the overall workflow of data collection and processing tasks.

### Running `crawl.py`
To run `crawl.py`, follow these steps:
1. Open a terminal.
2. Navigate to the project directory.
3. Execute the command:
   ```bash
   python crawl.py <url>
   ```
   Replace `<url>` with the actual URL you want to process.

This will initiate the crawling process for the specified URL, converting the JSON data to Markdown format.
