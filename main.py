import logging
import os
from datetime import datetime
from core.crawler import CrawlerConfiguration, WebsiteCrawler


def configure_application_logging():
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_directory = "logs"
    log_filename = f"crawler_operation_{current_time}.log"

    os.makedirs(log_directory, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_directory, log_filename)),
            logging.StreamHandler(),
        ],
    )


def execute_crawler_process():
    configure_application_logging()

    crawler_settings = CrawlerConfiguration(
        output_directory="data",
        request_timeout_seconds=15,
        max_retry_attempts=3,
        max_concurrent_workers=8,
        http_user_agent="AcademicResearchBot/1.0 (+https://university.edu)",
        max_filename_characters=200,
    )

    web_crawler = WebsiteCrawler(crawler_settings)
    initial_target_url = "https://www.civilopedia.net"

    try:
        web_crawler.log_handler.info(
            f"Initializing crawling process at: {initial_target_url}"
        )
        discovered_urls = web_crawler.crawl_using_breadth_first_search(
            initial_target_url
        )

        web_crawler.log_handler.info(
            f"Commencing download of {len(discovered_urls)} discovered pages"
        )
        html_content_map, failed_urls = web_crawler.fetch_and_persist_html_content(
            discovered_urls
        )

        if html_content_map:
            metadata_path = web_crawler.save_url_content_map(html_content_map)
            web_crawler.log_handler.info(f"Metadata stored at: {metadata_path}")

        if failed_urls:
            web_crawler.log_handler.warning(
                f"Failed to process {len(failed_urls)} URLs: {list(failed_urls)[:5]}..."
            )

        web_crawler.log_handler.info("Crawling operation completed successfully")

    except Exception as critical_error:
        web_crawler.log_handler.error(
            f"Critical operation failure: {str(critical_error)}", exc_info=True
        )
        raise


if __name__ == "__main__":
    execute_crawler_process()
