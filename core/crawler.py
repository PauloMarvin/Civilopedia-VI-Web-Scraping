import os
import re
import logging
import json
import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urljoin, urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor
from typing import Set, Tuple, Dict, Optional
from pydantic import BaseModel, Field, PositiveInt, constr


class CrawlerConfiguration(BaseModel):
    output_directory: str = Field(default="data")
    request_timeout_seconds: PositiveInt = Field(default=10)
    max_retry_attempts: PositiveInt = Field(default=3)
    max_concurrent_workers: PositiveInt = Field(default=5)
    http_user_agent: constr(strip_whitespace=True) = Field(default="WebCrawler/1.0")
    max_filename_characters: PositiveInt = Field(default=150)

    class Config:
        validate_default = True
        extra = "forbid"


class WebsiteCrawler:
    def __init__(self, configuration: CrawlerConfiguration):
        self.settings = configuration
        self.http_session = requests.Session()
        self.http_session.headers.update({"User-Agent": self.settings.http_user_agent})
        self.log_handler = logging.getLogger(self.__class__.__name__)
        self.log_handler.addHandler(logging.StreamHandler())
        self.log_handler.setLevel(logging.INFO)

    def _validate_url_domain(self, target_url: str, allowed_domain: str) -> bool:
        parsed_url = urlparse(target_url)
        return (
            parsed_url.netloc == allowed_domain
            and parsed_url.scheme in ["http", "https"]
            and not parsed_url.path.endswith((".pdf", ".jpg", ".png"))
        )

    def _standardize_url_format(self, raw_url: str) -> str:
        parsed_url = urlparse(raw_url)
        return urlunparse(parsed_url._replace(fragment="", query=""))

    def _generate_safe_filename(self, original_url: str) -> str:
        sanitized_string = re.sub(r"[^a-zA-Z0-9_-]", "_", original_url)
        truncated_name = sanitized_string[: self.settings.max_filename_characters]
        return (
            f"{truncated_name}.html"
            if len(truncated_name) < self.settings.max_filename_characters
            else f"{truncated_name[: self.settings.max_filename_characters]}.html"
        )

    def retrieve_webpage_content(self, page_url: str) -> Optional[str]:
        for retry_count in range(1, self.settings.max_retry_attempts + 1):
            try:
                response = self.http_session.get(
                    page_url, timeout=self.settings.request_timeout_seconds
                )
                response.raise_for_status()
                return response.text
            except requests.HTTPError as http_error:
                self.log_handler.error(
                    f"Attempt {retry_count} failed for {page_url}: HTTP {http_error.response.status_code}"
                )
            except requests.RequestException as request_error:
                self.log_handler.error(
                    f"Attempt {retry_count} failed for {page_url}: {str(request_error)}"
                )
            except Exception as unexpected_error:
                self.log_handler.error(
                    f"Unexpected error fetching {page_url}: {str(unexpected_error)}"
                )
                break
        return None

    def _write_content_to_file(
        self, file_content: str, subdirectory: str, output_filename: str
    ) -> str:
        full_output_path = os.path.join(self.settings.output_directory, subdirectory)
        os.makedirs(full_output_path, exist_ok=True)
        complete_file_path = os.path.join(full_output_path, output_filename)

        with open(complete_file_path, "w", encoding="utf-8") as file_object:
            file_object.write(file_content)
        return complete_file_path

    def save_formatted_html(self, source_url: str, html_data: str) -> str:
        try:
            parsed_html = BeautifulSoup(html_data, "html.parser")
            formatted_html = parsed_html.prettify()
            output_filename = self._generate_safe_filename(source_url)
            return self._write_content_to_file(
                formatted_html, "html_pages", output_filename
            )
        except Exception as save_error:
            self.log_handler.error(
                f"Error saving HTML for {source_url}: {str(save_error)}"
            )
            raise

    def extract_and_save_text_content(self, source_url: str, html_data: str) -> str:
        try:
            parsed_html = BeautifulSoup(html_data, "html.parser")
            text_content = parsed_html.get_text(separator="\n", strip=True)
            output_filename = self._generate_safe_filename(source_url).replace(
                ".html", ".txt"
            )
            return self._write_content_to_file(
                text_content, "text_content", output_filename
            )
        except Exception as extraction_error:
            self.log_handler.error(
                f"Error extracting text from {source_url}: {str(extraction_error)}"
            )
            raise

    def process_single_url(self, target_url: str) -> Tuple[str, Optional[str]]:
        html_content = self.retrieve_webpage_content(target_url)
        if not html_content:
            return (target_url, None)

        try:
            self.save_formatted_html(target_url, html_content)
            self.extract_and_save_text_content(target_url, html_content)
            return (target_url, html_content)
        except Exception:
            return (target_url, None)

    def fetch_and_persist_html_content(
        self, url_collection: Set[str]
    ) -> Tuple[Dict[str, str], Set[str]]:
        successful_crawls = {}
        failed_urls = set()

        with ThreadPoolExecutor(
            max_workers=self.settings.max_concurrent_workers
        ) as executor:
            processing_tasks = [
                executor.submit(self.process_single_url, url) for url in url_collection
            ]

            for task in processing_tasks:
                url, html_result = task.result()
                if html_result:
                    successful_crawls[url] = html_result
                    self.log_handler.info(f"Successfully processed: {url}")
                else:
                    failed_urls.add(url)

        return successful_crawls, failed_urls

    def discover_links_in_content(
        self, html_content: str, base_page_url: str
    ) -> Set[str]:
        parsed_html = BeautifulSoup(html_content, "html.parser")
        root_domain = urlparse(base_page_url).netloc
        found_links = set()

        for link_element in parsed_html.find_all("a", href=True):
            absolute_link = self._standardize_url_format(
                urljoin(base_page_url, link_element["href"])
            )
            if self._validate_url_domain(absolute_link, root_domain):
                found_links.add(absolute_link)

        return found_links

    def crawl_using_breadth_first_search(
        self, starting_url: str, max_crawl_depth: Optional[int] = None
    ) -> Set[str]:
        visited_urls = set()
        crawl_queue = deque([(self._standardize_url_format(starting_url), 0)])
        discovered_urls = set()

        while crawl_queue:
            current_url, current_depth = crawl_queue.popleft()

            if current_url in visited_urls or (
                max_crawl_depth is not None and current_depth > max_crawl_depth
            ):
                continue

            self.log_handler.info(
                f"Crawling: {current_url} (Current depth: {current_depth})"
            )
            page_content = self.retrieve_webpage_content(current_url)

            if not page_content:
                continue

            visited_urls.add(current_url)
            extracted_links = self.discover_links_in_content(page_content, current_url)

            for link in extracted_links:
                if link not in discovered_urls:
                    discovered_urls.add(link)
                    self.log_handler.debug(f"New URL discovered: {link}")

                if link not in visited_urls and (
                    max_crawl_depth is None or current_depth < max_crawl_depth
                ):
                    crawl_queue.append((link, current_depth + 1))

        return discovered_urls

    def save_url_content_map(
        self, content_data: dict, output_filename: str = "crawled_content.json"
    ) -> str:
        output_directory = os.path.join(
            self.settings.output_directory, "content_mappings"
        )
        os.makedirs(output_directory, exist_ok=True)
        full_file_path = os.path.join(output_directory, output_filename)

        try:
            with open(full_file_path, "w", encoding="utf-8") as output_file:
                json.dump(content_data, output_file, ensure_ascii=False, indent=4)
            return full_file_path
        except Exception as save_error:
            self.log_handler.error(f"Failed to save JSON data: {str(save_error)}")
            raise
