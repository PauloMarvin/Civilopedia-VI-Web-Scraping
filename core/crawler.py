import requests
from bs4 import BeautifulSoup
from collections import deque
from typing import Set, Tuple, Dict, Optional
import json


class WebCrawler:
    @staticmethod
    def fetch_content_with_retries(url: str, max_retries: int = 3) -> str:
        """Fetch the content of a URL with retry logic."""
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as error:
                print(f"Attempt {attempt} failed for {url}: {error}")
                if attempt == max_retries:
                    raise RuntimeError(
                        f"Failed to fetch {url} after {max_retries} attempts."
                    )
            except Exception as error:
                print(f"Unexpected error while fetching {url}: {error}")
                break

    @staticmethod
    def extract_links_from_html(html: str, base_url: str) -> Set[str]:
        """Extract all links from the provided HTML content."""
        soup = BeautifulSoup(html, "html.parser")
        anchor_tags = soup.find_all("a", href=True)

        links = set()
        for tag in anchor_tags:
            href = tag["href"]
            if href.startswith("/"):
                links.add(base_url.rstrip("/") + href)
            elif href.startswith(base_url):
                links.add(href)
        return links

    @staticmethod
    def crawl_links_using_bfs(
        start_url: str, max_depth: Optional[int] = None
    ) -> Set[str]:
        """Crawl links starting from the given URL using BFS with optional depth control."""
        visited_urls = set()
        discovered_links = set()
        urls_to_visit = deque([(start_url, 0)])

        while urls_to_visit:
            current_url, current_depth = urls_to_visit.popleft()

            if current_url in visited_urls:
                continue

            if max_depth is not None and current_depth > max_depth:
                continue

            try:
                page_content = WebCrawler.fetch_content_with_retries(current_url)
                extracted_links = WebCrawler.extract_links_from_html(
                    page_content, start_url
                )

                for link in extracted_links:
                    if link not in discovered_links:
                        print(f"Discovered new link at depth {current_depth}: {link}")
                        discovered_links.add(link)
                    if link not in visited_urls:
                        urls_to_visit.append(
                            (link, current_depth + 1)
                        )  # Increment depth for child links

            except RuntimeError as error:
                print(f"Error fetching {current_url}: {error}")

            visited_urls.add(current_url)

        return discovered_links

    @staticmethod
    def fetch_and_store_html(urls: Set[str]) -> Tuple[Dict[str, str], Set[str]]:
        """Fetch HTML content for a set of URLs and store it in a dictionary."""
        url_to_html_map = {}
        failed_urls = set()

        for url in urls:
            try:
                html_content = WebCrawler.fetch_content_with_retries(url)
                url_to_html_map[url] = html_content
                print(f"Successfully saved HTML for: {url}")
            except RuntimeError as error:
                print(f"Failed to fetch {url}: {error}")
                failed_urls.add(url)

        return url_to_html_map, failed_urls

    @staticmethod
    def save_dict_to_json_file(data: dict, file_path: str) -> None:
        """Save a dictionary to a JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f"Data successfully saved to JSON file: {file_path}")
        except (OSError, IOError) as error:
            print(f"Error saving JSON file {file_path}: {error}")

    @staticmethod
    def load_dict_from_json_file(file_path: str) -> Optional[dict]:
        """Load a dictionary from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except json.JSONDecodeError as error:
            print(f"Error decoding JSON file {file_path}: {error}")
        except (OSError, IOError) as error:
            print(f"Error reading JSON file {file_path}: {error}")
        return None
