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


# List of link texts to find corresponding URLs
link_texts_to_find = {
    "For the public": "https://www.bccnm.ca/Public/Pages/Default.aspx",
    "Licensed Practical Nurses": "https://www.bccnm.ca/LPN/Pages/Default.aspx",
    "Nurse Practitioners": "https://www.bccnm.ca/NP/Pages/Default.aspx",
    "Registered Nurses": "https://www.bccnm.ca/RN/Pages/Default.aspx",
    "Registered Psychiatric Nurses": "https://www.bccnm.ca/RPN/Pages/Default.aspx",
    "Midwives": "https://www.bccnm.ca/RM/Pages/Default.aspx",
    "About BCCNM": "https://www.bccnm.ca/BCCNM/Pages/Default.aspx"
}

# Async function to extract navigation links
async def extract_nav_links(page):
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('.crn-secondaryNavigation ul li a').forEach(a => {
            links.push(a.href);
        });
        return links;
    }''')

async def process_navigation_link(page, nav_link, file, processed_urls):
    if nav_link in processed_urls:
        return
    processed_urls.add(nav_link)

    logger.info(f"Processing navigation link: {nav_link}")
    content = await scrape_crn_content(page, nav_link)
    if content:
        file.write(f"URL: {nav_link}\n{content}")
        file.write("------------------------------------------------------------\n\n")
        # Extract and process further navigation links
        nav_links = await extract_nav_links(page)
        for next_nav_link in nav_links:
            await process_navigation_link(page, next_nav_link, file, processed_urls)

async def scrape_crn_content(page, url):
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        crn_content_div = soup.find('div', class_='crn-content col-xs-12 col-sm-9')
        content_text = ""

        if crn_content_div:
            # Extract text from various tags
            for element in crn_content_div.find_all(['h1', 'h2', 'p', 'ul']):
                # Handle lists separately to format list items
                if element.name == 'ul':
                    for li in element.find_all('li'):
                        content_text += f" - {li.get_text(strip=True)}\n"
                else:
                    content_text += f"{element.get_text(strip=True)}\n\n"

        return content_text if content_text else "Content not found or empty."
    except Exception as e:
        logger.error(f"Error scraping CRN content from {url}: {str(e)}")
        return None
    
async def scrape_british_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        processed_urls = set()

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            for link_text, url in link_texts_to_find.items():
                await process_navigation_link(page, url, temp_file, processed_urls)

            temp_file_path = temp_file.name  # Save the path to upload later

        await browser.close()
        logger.info("Scraping completed.")

        # Upload the temporary file to S3
        with open(temp_file_path, 'rb') as temp_file_to_upload:
            # Save the temporary file to S3 within the 'scraped_data' folder
            s3_file_name = "scraped_data/british/scraped_british_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
            logger.info(f"Temporary file {temp_file_path} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting temporary file {temp_file_path}: {e}")

# asyncio.run(scrape_british_site())
            

# @shared_task
# def scrape_british_site():
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(scrape_british_site())