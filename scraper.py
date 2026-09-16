
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Constants & Configuration
BASE_URL = "http://books.toscrape.com/catalogue/"
START_URL = "http://books.toscrape.com/catalogue/page-1.html"
TARGET_COUNT = 50
REQUEST_DELAY = 0.05  # Polite delay between requests (seconds)
OUTPUT_FILE = "products.csv"
RAW_OUTPUT_FILE = "products_raw.csv"

# Request headers to emulate standard browser traffic
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get_page(url: str, session: requests.Session = None, retries: int = 3, delay: float = REQUEST_DELAY) -> BeautifulSoup:
    """
    Sends an HTTP GET request to the specified URL with error handling and retries.
    Returns a BeautifulSoup object if successful, or None if failed.
    """
    http = session or requests
    for attempt in range(1, retries + 1):
        try:
            if delay > 0:
                time.sleep(delay)
            response = http.get(url, headers=HEADERS, timeout=10)
            
            # Check for HTTP status errors (4xx, 5xx)
            response.raise_for_status()
            
            # Ensure correct encoding (handles currency symbols properly)
            response.encoding = response.apparent_encoding or "utf-8"
            return BeautifulSoup(response.text, "html.parser")
            
        except requests.exceptions.RequestException as e:
            print(f"[Warning] Failed to fetch {url} (Attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(0.5 * attempt)  # Exponential backoff
            else:
                print(f"[Error] Max retries reached for URL: {url}")
                return None


def scrape_product(pod: BeautifulSoup, session: requests.Session = None, base_url: str = BASE_URL) -> dict:
    """
    Extracts product data from a catalog pod element and its detailed product page.
    Returns a dictionary of scraped product attributes.
    """
    try:
        # 1. Product Name (full title attribute from the <a> tag inside <h3>)
        title_tag = pod.select_one("h3 a")
        product_name = title_tag.get("title", "").strip() if title_tag else None
        if not product_name and title_tag:
            product_name = title_tag.get_text(strip=True)

        # 2. Product URL (resolved relative link to full absolute URL)
        relative_link = title_tag.get("href", "") if title_tag else ""
        product_url = urljoin(base_url, relative_link)

        # 3. Price (as displayed on the page)
        price_tag = pod.select_one("p.price_color")
        price = price_tag.get_text(strip=True) if price_tag else None

        # 4. Rating (CSS class name: 'star-rating Three' -> 'Three')
        rating_tag = pod.select_one("p.star-rating")
        rating = None
        if rating_tag:
            rating_classes = [c for c in rating_tag.get("class", []) if c != "star-rating"]
            rating = rating_classes[0] if rating_classes else None

        # 5. Detail Page Attributes: Category, Availability & Number of Reviews
        category = "Unknown"
        availability = "Unknown"
        num_reviews = "0"

        if product_url:
            detail_soup = get_page(product_url, session=session, delay=REQUEST_DELAY)
            if detail_soup:
                # Category from breadcrumbs (Home > Books > [Category] > Title)
                breadcrumb_items = detail_soup.select("ul.breadcrumb li")
                if len(breadcrumb_items) >= 3:
                    category = breadcrumb_items[2].get_text(strip=True)

                # Availability & Number of Reviews from the Product Information table
                info_table = detail_soup.select_one("table.table-striped")
                if info_table:
                    for row in info_table.select("tr"):
                        th_text = row.th.get_text(strip=True) if row.th else ""
                        if "Availability" in th_text:
                            availability = row.td.get_text(strip=True) if row.td else "Unknown"
                        elif "Number of reviews" in th_text:
                            num_reviews = row.td.get_text(strip=True) if row.td else "0"

        return {
            "product_name": product_name,
            "price": price,
            "rating": rating,
            "availability": availability,
            "number_of_reviews": num_reviews,
            "category": category,
            "product_url": product_url
        }

    except Exception as err:
        print(f"[Warning] Error parsing product pod: {err}")
        return None


def scrape_page(soup: BeautifulSoup, session: requests.Session, collected_data: list, 
                collected_urls: set, target_count: int = TARGET_COUNT) -> int:
    """
    Finds and processes all product pods on a given catalog page.
    Appends unique items to collected_data until target_count is reached.
    """
    pods = soup.select("article.product_pod")
    for pod in pods:
        if len(collected_data) >= target_count:
            break

        # Check URL uniqueness before scraping detail page
        title_tag = pod.select_one("h3 a")
        rel_link = title_tag.get("href", "") if title_tag else ""
        prod_url = urljoin(BASE_URL, rel_link)

        if prod_url in collected_urls:
            continue  # Skip duplicate

        product_data = scrape_product(pod, session=session)
        if product_data and product_data.get("product_name"):
            collected_data.append(product_data)
            collected_urls.add(product_data["product_url"])
            print(f"Scraped {len(collected_data)}/{target_count} products: {product_data['product_name'][:40]}...")

    return len(collected_data)


def save_data(df: pd.DataFrame, filename: str) -> None:
    """
    Saves a DataFrame to a CSV file encoded in UTF-8 without the index column.
    """
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"[Success] Saved {len(df)} records to '{filename}'")


def main():
    """
    Main orchestrator function:
    1. Initializes HTTP session.
    2. Paginates through catalog pages until 500 unique products are scraped.
    3. Saves dataset directly to products.csv and products_raw.csv.
    4. Displays dataset preview.
    """
    print("=" * 60)
    print(f"Starting Scraper: Target = {TARGET_COUNT} Products")
    print("=" * 60)

    session = requests.Session()
    collected_data = []
    collected_urls = set()
    page_number = 1

    start_time = time.time()

    # Pagination loop
    while len(collected_data) < TARGET_COUNT:
        page_url = f"http://books.toscrape.com/catalogue/page-{page_number}.html"
        print(f"\n[Page {page_number}] Fetching catalog page: {page_url}")
        
        soup = get_page(page_url, session=session)
        if not soup:
            print(f"[Info] Could not fetch page {page_number}. Ending pagination.")
            break

        # Check if products exist on page
        pods = soup.select("article.product_pod")
        if not pods:
            print(f"[Info] No more products found on page {page_number}. Ending pagination.")
            break

        # Scrape products from the current page
        scrape_page(soup, session, collected_data, collected_urls, target_count=TARGET_COUNT)

        # Check if there is a 'next' button for pagination
        next_btn = soup.select_one("li.next a")
        if not next_btn and len(collected_data) < TARGET_COUNT:
            print("[Info] No next page available.")
            break

        page_number += 1

    elapsed_time = round(time.time() - start_time, 2)
    print("\n" + "=" * 60)
    print(f"Scraping Finished! Total Products Scraped: {len(collected_data)} in {elapsed_time}s")
    print("=" * 60)

    # Convert to DataFrame
    df = pd.DataFrame(collected_data)

    # Save to CSV files
    save_data(df, OUTPUT_FILE)
    save_data(df, RAW_OUTPUT_FILE)

    # Display preview
    print("\n--- Scraped Dataset Preview ---")
    print(df.head())
    print("\n--- Dataset Info ---")
    print(df.info())


if __name__ == "__main__":
    main()
