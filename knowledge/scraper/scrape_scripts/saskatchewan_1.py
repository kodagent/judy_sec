import asyncio
import tempfile
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from playwright.async_api import async_playwright

from chatbackend.configs.logging_config import configure_logger
from knowledge.scraper.scraper_utils import download_pdf, sanitize_filename

logger = configure_logger(__name__)

# Base URL
base_url = "https://www.crns.ca/"

async def extract_navigation_links(page):
    # Extracts both primary and sub-menu links
    await page.goto(base_url, timeout=60000)
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('#primary-menu > li').forEach(menuItem => {
            const a = menuItem.querySelector('a');
            const subMenuLinks = [];
            menuItem.querySelectorAll('.sub-menu li a').forEach(subItem => {
                subMenuLinks.push({text: subItem.innerText.trim(), href: subItem.href});
            });
            links.push({text: a.innerText.trim(), href: a.href, subLinks: subMenuLinks});
        });
        return links;
    }''')

async def scrape_page_content(page, url):
    # Scrapes the content of the page based on the provided structure
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        main_content = soup.find('div', class_='entry-content')
        content_text = ""

        if main_content:
            for element in main_content.find_all(True, recursive=False):
                content_text += f"{element.get_text(strip=True)}\n\n"
        else:
            content_text += "Main content not found.\n"

        return content_text
    except Exception as e:
        logger.error(f"Error scraping content from {url}: {str(e)}")
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

async def scrape_crns_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        processed_urls = set()

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            navigation_links = await extract_navigation_links(page)
            for link in navigation_links:
                await process_page(page, link['href'], temp_file, processed_urls)
                for sub_link in link.get('subLinks', []):
                    await process_page(page, sub_link['href'], temp_file, processed_urls)

            temp_file_path = temp_file.name  # Save the path to upload later

        await browser.close()
        logger.info("Scraping completed.")

        # Upload the temporary file to S3
        with open(temp_file_path, 'rb') as temp_file_to_upload:
            s3_file_name = "scraped_data/scraped_crns_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

# asyncio.run(scrape_crns_site())