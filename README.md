# Web Crawler for Civilopedia

This project implements a web crawler that collects and stores the HTML content
of web pages, focusing initially on the site [Civilopedia.net](https://www.civilopedia.net).
The collected HTMLs will be used as input for the [Docling](https://github.com/DS4SD/docling) framework, assisting in projects related to language models (LLM).

## Features

The web crawler offers the following main features:

1. **Recursive Link Crawling (BFS)**:
   - Explores pages starting from an initial URL, discovering and storing internal links on the site.

2. **HTML Content Collection**:
   - Makes HTTP requests to obtain the HTML content of the discovered pages.

3. **Data Storage**:
   - Saves the collected HTMLs in a JSON file for later use.

4. **Retry Mechanism**:
   - Implements retry logic to handle failures in fetching page content.

5. **Error Logging for Links**:
   - Logs links that could not be accessed.

## Project Structure

- **core/crawler.py**:
  Contains the `WebCrawler` class with all crawler functionalities.

- **main.py**:
  Main script that orchestrates the process of crawling, collecting, and storing data.

## Dependencies

- Python 3.8+
- Libraries:
  - `requests`: For making HTTP requests.
  - `beautifulsoup4`: For parsing and extracting links from HTML pages.
  - `json`: For saving and loading collected data.

## How to Use

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/web-crawler-civilopedia.git
   cd web-crawler-civilopedia
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Run the crawler**:
   ```bash
   poetry run python main.py
   ```

4. **Results**:
   - Discovered links will be displayed in the console.
   - Collected HTMLs will be saved in the file `data/civilopedia_all_links_html.json`.

## Output File

- **`data/civilopedia_all_links_html.json`**:
  - A JSON file containing the HTML content of all collected pages.
  - Format:
    ```json
    {
        "https://www.civilopedia.net/page1": "<html>...</html>",
        "https://www.civilopedia.net/page2": "<html>...</html>",
        ...
    }
    ```

- Links that fail during collection will be logged in the console.
