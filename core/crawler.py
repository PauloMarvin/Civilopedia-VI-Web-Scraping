import os
import requests
from bs4 import BeautifulSoup
from collections import deque
from typing import Set, Tuple, Dict, Optional
import json


class WebCrawler:
    @staticmethod
    def fetch_html(url: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.text
            except requests.RequestException as error:
                print(f"Attempt {attempt} failed for {url}: {error}")
                if attempt == max_retries:
                    print(f"Failed to fetch {url} after {max_retries} attempts.")
            except Exception as error:
                print(f"Unexpected error while fetching {url}: {error}")
                break
        return None

    @staticmethod
    def sanitize_filename(url: str) -> str:
        return (
            url.replace("://", "_")
            .replace("/", "_")
            .replace("?", "_")
            .replace("&", "_")
        )

    @staticmethod
    def save_html_to_file(url: str, html_content: str, output_dir: str) -> None:
        try:
            os.makedirs(output_dir, exist_ok=True)
            file_name = WebCrawler.sanitize_filename(url) + ".html"
            file_path = os.path.join(output_dir, file_name)

            soup = BeautifulSoup(html_content, "html.parser")
            formatted_html = soup.prettify()

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(formatted_html)
            print(f"Formatted HTML saved to {file_path}")
        except (OSError, IOError) as error:
            print(f"Error saving formatted HTML file for {url}: {error}")

    @staticmethod
    def fetch_and_store_html_in_dict(urls: Set[str]) -> Tuple[Dict[str, str], Set[str]]:
        url_to_html_map = {}
        failed_urls = set()

        for url in urls:
            html_content = WebCrawler.fetch_html(url)
            if html_content:
                url_to_html_map[url] = html_content
                print(f"HTML fetched and stored for: {url}")
            else:
                failed_urls.add(url)

        return url_to_html_map, failed_urls

    @staticmethod
    def extract_links_from_html(html: str, base_url: str) -> Set[str]:
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
        visited_urls = set()
        discovered_links = set()
        urls_to_visit = deque([(start_url, 0)])

        while urls_to_visit:
            current_url, current_depth = urls_to_visit.popleft()

            if current_url in visited_urls:
                continue

            if max_depth is not None and current_depth > max_depth:
                continue

            html_content = WebCrawler.fetch_html(current_url)
            if html_content:
                extracted_links = WebCrawler.extract_links_from_html(
                    html_content, start_url
                )

                for link in extracted_links:
                    if link not in discovered_links:
                        print(f"Discovered new link at depth {current_depth}: {link}")
                        discovered_links.add(link)
                    if link not in visited_urls:
                        urls_to_visit.append(
                            (link, current_depth + 1)
                        )

            visited_urls.add(current_url)

        return discovered_links

    @staticmethod
    def save_dict_to_json_file(data: dict, file_path: str) -> None:
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print(f"Data successfully saved to JSON file: {file_path}")
        except (OSError, IOError) as error:
            print(f"Error saving JSON file {file_path}: {error}")

    @staticmethod
    def load_dict_from_json_file(file_path: str) -> Optional[dict]:
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

    @staticmethod
    def save_texts_from_htmls(html_dict: Dict[str, str], output_dir: str) -> None:
        try:
            os.makedirs(output_dir, exist_ok=True)

            for url, html_content in html_dict.items():
                file_name = WebCrawler.sanitize_filename(url) + ".txt"
                file_path = os.path.join(output_dir, file_name)

                soup = BeautifulSoup(html_content, "html.parser")
                text = soup.get_text(separator="\n", strip=True)

                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(text)
                print(f"Text extracted and saved to {file_path}")
        except (OSError, IOError) as error:
            print(f"Error saving text files: {error}")