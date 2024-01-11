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
base_url = "https://www.cno.org/en/"


# List of link texts to find corresponding URLs
link_texts_to_find = [
    "What is CNO?",
    "Protect the Public",
    "Become a Nurse",
    "Standards & Learning",
    "Quality Assurance",
    "The Standard",
    "Maintain Your Membership"
]

    
# Async function to get content using Playwright
async def scrape_html_content(page, url):
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        main_content = soup.find('main', {'role': 'main'})
        content_text = ""

        if main_content:
            title = main_content.find('h1')
            if title:
                content_text += f"Title: {title.get_text(strip=True)}\n\n"
            for content in main_content.find_all(['p', 'ul'], recursive=False):
                content_text += f"{content.get_text(strip=True)}\n\n"
        else:
            content_text += "Main content not found.\n"

        return content_text
    except Exception as e:
        logger.error(f"Error scraping content from {url}: {str(e)}")
        return None

# Async function to scrape category and sub-category links
async def scrape_category_links(page, url):
    # Modify this function to handle subcategories
    await page.goto(url, timeout=60000)
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('.nav-secondary li a').forEach(a => {
            const parentLi = a.closest('li');
            const subLinks = [];
            if (parentLi && parentLi.querySelector('ul')) {
                parentLi.querySelectorAll('ul li a').forEach(subA => subLinks.push({text: subA.innerText.trim(), href: subA.href}));
            }
            links.push({text: a.innerText.trim(), href: a.href, subLinks});
        });
        return links;
    }''')

async def process_category(page, category_url, file, processed_urls, title=""):
    if category_url in processed_urls or not category_url.startswith("http"):
        return
    processed_urls.add(category_url)

    if category_url.endswith('.pdf'):
        pdf_name = f"{sanitize_filename(title)}.pdf"
        pdf_path = f"ontario/{pdf_name}"
        await download_pdf(category_url, pdf_path)
    else:
        logger.info(f"Processing category: {category_url}")
        content = await scrape_html_content(page, category_url)
        if content:
            file.write(f"Page: {title}\nURL: {category_url}\n{content}")
            file.write("------------------------------------------------------------\n\n")
        category_links = await scrape_category_links(page, category_url)
        for cat_link in category_links:
            await process_category(page, cat_link['href'], file, processed_urls, cat_link['text'])
            for sub_link in cat_link.get('subLinks', []):
                await process_category(page, sub_link['href'], file, processed_urls, sub_link['text'])

async def scrape_ontario_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        processed_urls = set()

        await page.goto(base_url, timeout=60000)
        main_links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText, href: a.href}))
        }''')

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            for link in main_links:
                if link['text'].strip() in link_texts_to_find:
                    absolute_url = urljoin(base_url, link['href'])
                    await process_category(page, absolute_url, temp_file, processed_urls)

            temp_file_path = temp_file.name  # Save the path to upload later

        await browser.close()
        logger.info("Scraping completed.")

        # Upload the temporary file to S3
        with open(temp_file_path, 'rb') as temp_file_to_upload:
            # Save the temporary file to S3 within the 'scraped_data' folder
            s3_file_name = "scraped_data/ontario/scraped_ontario_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
            logger.info(f"Temporary file {temp_file_path} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting temporary file {temp_file_path}: {e}")

# asyncio.run(scrape_ontario_site())


# @shared_task
# def scrape_ontario_site():
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(scrape_ontario_site())