import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time


# =========================
# CONFIG
# =========================
BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"
OUTPUT_DIR = "output"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# =========================
# SCRAPE SINGLE PAGE
# =========================
def scrape_page(page_number):
    url = BASE_URL.format(page_number)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching page {page_number}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.find_all("article", class_="product_pod")

    page_data = []

    for book in books:
        try:
            name = book.h3.a["title"]

            price = book.find("p", class_="price_color").text.strip()

            availability = book.find(
                "p", class_="instock availability"
            ).text.strip()

            rating_class = book.p["class"][1]
            rating_map = {
                "One": 1,
                "Two": 2,
                "Three": 3,
                "Four": 4,
                "Five": 5
            }
            rating = rating_map.get(rating_class, None)

            relative_link = book.h3.a["href"]
            full_link = "http://books.toscrape.com/catalogue/" + relative_link

            page_data.append({
                "Product Name": name,
                "Price": price,
                "Rating (out of 5)": rating,
                "Availability": availability,
                "Product Link": full_link
            })

        except Exception as e:
            print(f"⚠️ Skipping item due to error: {e}")

    return page_data


# =========================
# SCRAPE MULTIPLE PAGES
# =========================
def scrape_all_pages(total_pages=5):
    all_data = []

    for page in range(1, total_pages + 1):
        print(f"📄 Scraping page {page}...")
        page_data = scrape_page(page)
        all_data.extend(page_data)
        time.sleep(1)  # polite delay

    return all_data


# =========================
# DATA CLEANING
# =========================
def clean_data(df):
    # Remove duplicates
    df.drop_duplicates(inplace=True)

    # Handle missing values
    df.fillna("N/A", inplace=True)

    # Convert price to numeric
    df["Price"] = df["Price"].str.replace("£", "", regex=False)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").round(2)

    # Convert availability to clean format
    df["Availability"] = df["Availability"].str.strip()

    # Reset index
    df.reset_index(drop=True, inplace=True)

    return df


# =========================
# SAVE DATA
# =========================
def save_data(df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    csv_path = os.path.join(OUTPUT_DIR, "products.csv")
    json_path = os.path.join(OUTPUT_DIR, "products.json")
    excel_path = os.path.join(OUTPUT_DIR, "products.xlsx")

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=4)
    df.to_excel(excel_path, index=False)

    print("\n✅ Files saved successfully:")
    print(f"📁 CSV: {csv_path}")
    print(f"📁 JSON: {json_path}")
    print(f"📁 Excel: {excel_path}")


# =========================
# MAIN PIPELINE
# =========================
def main():
    print("🚀 Starting E-commerce Scraper...\n")

    raw_data = scrape_all_pages(total_pages=5)

    df = pd.DataFrame(raw_data)

    if df.empty:
        print("❌ No data scraped. Exiting...")
        return

    df = clean_data(df)

    save_data(df)

    print(f"\n📊 Total products scraped: {len(df)}")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()