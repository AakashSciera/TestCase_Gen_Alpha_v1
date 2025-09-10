import os
import argparse
from playwright.sync_api import sync_playwright
import time

def scrape_website(url, web_name):
    """
    Navigates to a URL, takes a full-page screenshot, and saves the DOM using Playwright.

    Args:
        url (str): The URL to scrape.
        web_name (str): A name to use for the output files.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the URL
        page.goto(url, wait_until="networkidle")

        # Create a directory to save the output
        output_dir = "scraped_data"
        os.makedirs(output_dir, exist_ok=True)

        # Save the full-page screenshot
        screenshot_path = os.path.join(output_dir, f"{web_name}_screenshot.png")
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Full-page screenshot saved to {screenshot_path}")

        # Save the DOM
        dom_path = os.path.join(output_dir, f"{web_name}_dom.html")
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        print(f"DOM saved to {dom_path}")

        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape a website using Playwright.")
    parser.add_argument("url", help="The URL to scrape.")
    parser.add_argument("web_name", help="A name for the output files.")
    args = parser.parse_args()

    print("Scraping website...")
    scrape_website(args.url, args.web_name)