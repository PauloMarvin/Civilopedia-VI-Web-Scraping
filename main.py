from core.crawler import WebCrawler

def main():
    start_url = "https://www.civilopedia.net"
    max_depth = 1
    html_output_dir = "data/htmls"
    text_output_dir = "data/htmls_text"
    dict_output_path = "data/html_dicts/html_content.json"

    print(f"Starting the crawl from: {start_url} with max depth: {max_depth}\n")

    all_discovered_links = WebCrawler.crawl_links_using_bfs(start_url, max_depth)
    print(f"\nTotal links discovered: {len(all_discovered_links)}")

    print(f"\nStarting to download HTML content for {len(all_discovered_links)} links...")
    url_to_html_map, failed_links = WebCrawler.fetch_and_store_html_in_dict(all_discovered_links)

    if failed_links:
        print(f"\nFailed to fetch {len(failed_links)} links. Check the logs for more details.")
    else:
        print("\nAll links were successfully fetched.")

    print(f"\nSaving HTML content to {html_output_dir}...")
    for url, html_content in url_to_html_map.items():
        WebCrawler.save_html_to_file(url, html_content, html_output_dir)

    print(f"\nExtracting and saving text content to {text_output_dir}...")
    WebCrawler.save_texts_from_htmls(url_to_html_map, text_output_dir)

    print(f"\nSaving HTML content dictionary to {dict_output_path}...")
    WebCrawler.save_dict_to_json_file(url_to_html_map, dict_output_path)

    print("\nProcess completed successfully.")

if __name__ == "__main__":
    main()
