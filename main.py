from core.crawler import WebCrawler

def main():
    start_url = "https://www.civilopedia.net"
    print(f"Starting the crawl from: {start_url}\n")

    all_discovered_links = WebCrawler.crawl_links_using_bfs(start_url)
    print(f"\nTotal links discovered: {len(all_discovered_links)}")

    print(f"\nStarting to download HTML content for {len(all_discovered_links)} links...")
    html_contents, failed_links = WebCrawler.fetch_and_store_html(all_discovered_links)

    WebCrawler.save_dict_to_json_file(
        data=html_contents, file_path="data/civilopedia_all_links_html.json"
    )

    if failed_links:
        print(f"\nFailed to fetch {len(failed_links)} links. Check the logs for more details.")
    else:
        print("\nAll links were successfully fetched.")

if __name__ == "__main__":
    main()