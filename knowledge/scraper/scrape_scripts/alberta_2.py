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

# List of link texts to find corresponding URLs
urls_to_scrape = [
    "https://www.clpna.com/for-the-public/public-registry-employer-verification/",
    "https://www.clpna.com/about-the-clpna/council-governance/"
]

# Function to scrape main content
async def scrape_main_content(page, url, scraped_urls, file):
    if url in scraped_urls:
        return
    scraped_urls.add(url)

    if url.endswith('.pdf'):
        pdf_name = sanitize_filename(url.split('/')[-1])
        pdf_path = f"alberta_2/pdfs/{pdf_name}"
        await download_pdf(url, pdf_path)
    else:
        try:
            await page.goto(url, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            main_content = soup.select('div.w-full section')

            content_text = f"URL: {url}\n"
            for section in main_content:
                content_text += f"{section.get_text(strip=True)}\n\n"

            file.write(content_text)
            file.write("------------------------------------------------------------\n\n")

            await scrape_nav_links(page, url, scraped_urls, file)
        except Exception as e:
            logger.error(f"Error scraping content from {url}: {str(e)}")

# Function to scrape and follow navigation links
async def scrape_nav_links(page, url, scraped_urls, file):
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        nav_links = soup.select('div.dropdown ul li a')

        for a in nav_links:
            link = a['href']
            if link and not link.startswith('http'):
                link = urljoin(url, link)
            if link not in scraped_urls:
                await scrape_main_content(page, link, scraped_urls, file)
    except Exception as e:
        logger.error(f"Error scraping navigation links from {url}: {str(e)}")

# Main scraping function
async def scrape_alberta_site_2():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        scraped_urls = set()
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            for base_url in urls_to_scrape:
                await scrape_main_content(page, base_url, scraped_urls, temp_file)

            temp_file_path = temp_file.name

        await browser.close()

        with open(temp_file_path, 'rb') as temp_file_to_upload:
            s3_file_name = "scraped_data/alberta_2/scraped_content/scraped_alberta_2_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
            logger.info(f"Temporary file {temp_file_path} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting temporary file {temp_file_path}: {e}")

# # Run the scraping function
# asyncio.run(scrape_alberta_site_2())
            
# @shared_task
# def scrape_alberta_site_2():
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(scrape_alberta_site_2())