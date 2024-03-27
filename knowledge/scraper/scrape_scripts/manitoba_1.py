import asyncio
import os
import tempfile

from bs4 import BeautifulSoup
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from playwright.async_api import async_playwright

from chatbackend.configs.logging_config import configure_logger
from knowledge.scraper.scraper_utils import download_pdf, sanitize_filename

logger = configure_logger(__name__)

# Base URL
base_url = "https://www.crnm.mb.ca/"

EXCLUDED_URLS = [
    "https://www.crnm.mb.ca/",
    "https://www.crnm.mb.ca/#skipNavigation",
    "https://www.crnm.mb.ca/news/",
    "https://www.crnm.mb.ca/news/#skipNavigation",
    "https://www.crnm.mb.ca/rns-nps/resource-library/",
    "https://www.crnm.mb.ca/rns-nps/resource-library/#skipNavigation",
    "https://www.crnm.mb.ca/contact/",
    "https://www.crnm.mb.ca/contact/#skipNavigation",
]

async def extract_nav_links(page):
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('#mega-menu-main-menu .mega-menu-item a').forEach(a => {
            links.push({text: a.innerText.trim(), href: a.href});
        });
        return links;
    }''')

async def extract_all_links(page):
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            links.push(a.href);
        });
        return links.filter(href => href.startsWith(document.location.origin));
    }''')

async def scrape_html_content(page, url):
    try:
        await page.goto(url, timeout=60000)
        # Wait for the main content to be loaded
        await page.wait_for_selector('main.section-page', timeout=60000)

        content_html = await page.content()
        soup = BeautifulSoup(content_html, 'html.parser')

        # Adjust the selector according to the structure of the content you want to scrape
        main_content = soup.select_one('main.section-page')
        content_text = ""

        if main_content:
            for element in main_content.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'li', 'a']):
                # Check if the element is a link to a PDF
                if element.name == 'a' and 'href' in element.attrs and element['href'].endswith('.pdf'):
                    pdf_url = element['href']
                    pdf_name = f"{sanitize_filename(element.get_text(strip=True))}.pdf"
                    pdf_path = f"manitoba_1/pdfs/{pdf_name}"
                    await download_pdf(pdf_url, pdf_path)
                else:
                    content_text += f"{element.get_text(' ', strip=True)}\n\n"
        else:
            content_text = "Main content not found.\n"

        return content_text
    except Exception as e:
        logger.info(f"Error scraping content from {url}: {str(e)}")
        return None

async def process_page(page, url, temp_file, processed_urls):
    if url in processed_urls or not url.startswith(base_url):
        return
    if "#skipNavigation" in url or url in EXCLUDED_URLS:
        return  
    processed_urls.add(url)

    if url.endswith('.pdf'):
        logger.info(f"Processing pdf: {url}")
        pdf_url = url
        pdf_name = sanitize_filename(url.rsplit('/', 1)[-1])
        pdf_path = f"manitoba_1/pdfs/{pdf_name}"
        logger.info(f"PDF found: {pdf_path}")
        await download_pdf(pdf_url, pdf_path)
    else:
        logger.info(f"Processing page: {url}")
        content = await scrape_html_content(page, url)
        if content:
            temp_file.write(f"URL: {url}\n{content}")
            temp_file.write("------------------------------------------------------------\n\n")

        all_links = await extract_all_links(page)
        for link in all_links:
            await process_page(page, link, temp_file, processed_urls)

async def scrape_crnm_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(base_url, timeout=60000)
        await page.wait_for_selector('#mega-menu-main-menu .mega-menu-item a', timeout=30000)

        processed_urls = set()
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            nav_links = await extract_nav_links(page)
            for nav_link in nav_links:
                await process_page(page, nav_link['href'], temp_file, processed_urls)

            temp_file_path = temp_file.name

        await browser.close()
        logger.info("Scraping completed.")

        # Upload the temporary file to S3
        with open(temp_file_path, 'rb') as temp_file_to_upload:
            s3_file_name = "scraped_data/manitoba_1/scraped_content/scraped_crnm_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
            logger.info(f"Temporary file {temp_file_path} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting temporary file {temp_file_path}: {e}")
            
# Run the scraping process
@shared_task
def scrape_crnm_site_task():
    asyncio.run(scrape_crnm_site())


# @shared_task
# def scrape_crnm_site():
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(scrape_crnm_site())