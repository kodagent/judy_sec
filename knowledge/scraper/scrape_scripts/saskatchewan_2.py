import asyncio
import os
import tempfile
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from playwright.async_api import async_playwright

from chatbackend.configs.logging_config import configure_logger
from knowledge.scraper.scraper_utils import download_pdf, sanitize_filename

logger = configure_logger(__name__)

# Base URL of the website
base_url = "https://clpns.com/"

# Function to scrape dropdown menu links
async def scrape_dropdown_links(page):
    dropdown_links = []

    # Locate all first-level menu UL elements
    menu_elements = await page.query_selector_all("ul.x-menu-first-level")

    for menu in menu_elements:
        # Get all 'a' elements from each first-level menu
        links = await menu.query_selector_all("a")
        for link in links:
            href = await link.get_attribute("href")
            # Append to the list if it's a valid link
            if href and href.startswith("http"):
                dropdown_links.append(href)

    return dropdown_links


async def extract_page_links(page):
    # Extracts all links from the current page content
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            if (a.href) {
                links.push(a.href);
            }
        });
        return links;
    }''')

# Function to scrape the main content of a page
async def scrape_page_content(page, url):
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')

        # Find the main content area
        main_content_area = soup.find('main', {'role': 'main'})
        if not main_content_area:
            return "Main content not found"

        # Extracting specific content inside main tag
        extracted_content = ""
        for element in main_content_area.find_all(['p', 'h1', 'h2', 'ul', 'li']):
            extracted_content += str(element) + "\n\n"

        return extracted_content
    except Exception as e:
        print(f"Error scraping content from {url}: {str(e)}")
        return None

async def process_page(page, url, file, processed_urls, depth, max_depth=10):
    # Process each page: scrape content, download PDFs, and process sub-pages
    if url in processed_urls or not url.startswith(base_url):
        return
    processed_urls.add(url)

    if url.endswith('.pdf'):
        pdf_name = f"{sanitize_filename(url)}.pdf"
        pdf_path = f"saskatchewan_2/pdfs/{pdf_name}"
        await download_pdf(url, pdf_path)
    else:
        logger.info(f"Processing page: {url}")
        content = await scrape_page_content(page, url)
        if content:
            file.write(f"URL: {url}\n{content}")
            file.write("------------------------------------------------------------\n\n")

            if depth <= max_depth:
                child_links = await extract_page_links(page)
                for child_url in child_links:
                    await process_page(page, child_url, file, processed_urls, depth + 1, max_depth)

# Main scraping function
async def scrape_clpns_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        processed_urls = set()

        # Navigate to the base URL
        await page.goto(base_url, timeout=60000)

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            dropdown_links = await scrape_dropdown_links(page)
            for link in dropdown_links:
                await process_page(page, link, temp_file, processed_urls, depth=1)

            temp_file_path = temp_file.name  # Save the path to upload later

        await browser.close()
        logger.info("Scraping completed.")

        # Upload the temporary file to S3
        with open(temp_file_path, 'rb') as temp_file_to_upload:
            s3_file_name = "scraped_data/saskatchewan_2/scraped_content/scraped_clpns_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
            logger.info(f"Temporary file {temp_file_path} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting temporary file {temp_file_path}: {e}")

# Run the scraper
@shared_task
def scrape_clpns_site_task():
    asyncio.run(scrape_clpns_site())


# @shared_task
# def scrape_clpns_site():
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(scrape_clpns_site())