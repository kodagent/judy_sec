import asyncio
import tempfile
from urllib.parse import urljoin

from bs4 import BeautifulSoup
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
    # Trigger all dropdowns
    nav_links = await page.query_selector_all('.x-anchor.x-anchor-toggle')
    for nav_link in nav_links:
        # Click the nav link to show the dropdown
        await nav_link.click()

        # Locate dropdown elements within the clicked nav link and extract links
        dropdown_elements = await nav_link.query_selector_all(".x-dropdown")
        for element in dropdown_elements:
            links = await element.query_selector_all("a")
            for link in links:
                href = await link.get_attribute("href")
                if href and href.startswith("http") and href not in dropdown_links:
                    dropdown_links.append(href)

    return dropdown_links

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

async def process_page(page, url, file, processed_urls):
    # Process each page: scrape content, download PDFs, and process sub-pages
    if url in processed_urls or not url.startswith(base_url):
        return
    processed_urls.add(url)

    if url.endswith('.pdf'):
        pdf_name = f"{sanitize_filename(url)}.pdf"
        await download_pdf(url, pdf_name)
    else:
        logger.info(f"Processing page: {url}")
        content = await scrape_page_content(page, url)
        if content:

            logger.info(f"URL: {url}\n{content}")
            logger.info("------------------------------------------------------------\n\n")

            file.write(f"URL: {url}\n{content}")
            file.write("------------------------------------------------------------\n\n")

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
                await process_page(page, link, temp_file, processed_urls)

            temp_file_path = temp_file.name  # Save the path to upload later

        await browser.close()
        logger.info("Scraping completed.")

        # Upload the temporary file to S3
        with open(temp_file_path, 'rb') as temp_file_to_upload:
            s3_file_name = "scraped_data/scraped_clpns_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")


# # Run the scraper
# asyncio.run(scrape_clpns_site())
