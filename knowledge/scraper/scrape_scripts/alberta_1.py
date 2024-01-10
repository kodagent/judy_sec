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


# List of link texts to find corresponding URLs
urls_to_scrape = [
    "https://nurses.ab.ca/protect-the-public/",
    "https://nurses.ab.ca/how-we-operate/",
    "https://connect.nurses.ab.ca/home",
]

# Function to scrape main content
async def scrape_main_content(page, url, scraped_urls, file):
    if url in scraped_urls:
        return
    scraped_urls.add(url)

    if url.endswith('.pdf'):
        pdf_name = sanitize_filename(url.split('/')[-1])
        await download_pdf(url, pdf_name)
    else:
        try:
            await page.goto(url, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            main_content = soup.find_all('div', class_='row')

            content_text = f"URL: {url}\n"
            for content_div in main_content:
                title = content_div.find('h4', class_='title')
                if title:
                    content_text += f"Title: {title.get_text(strip=True)}\n\n"
                paragraphs = content_div.find_all('p')
                for paragraph in paragraphs:
                    content_text += f"{paragraph.get_text(strip=True)}\n\n"

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
        nav_links_div = soup.find_all('div', class_='row row-cols-1 row-cols-md-3 g-4 pt-3')

        for div in nav_links_div:
            a_tags = div.find_all('a')
            for a in a_tags:
                link = a['href']
                if link and not link.startswith('http'):
                    link = urljoin(url, link)
                if link not in scraped_urls:
                    await scrape_main_content(page, link, scraped_urls, file)
    except Exception as e:
        logger.error(f"Error scraping navigation links from {url}: {str(e)}")
    

# Main scraping function
async def scrape_alberta_site_1():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        scraped_urls = set()
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            for base_url in urls_to_scrape:
                await scrape_main_content(page, base_url, scraped_urls, temp_file)

            temp_file_path = temp_file.name  # Save the path for later use

        await browser.close()

        # Upload the temporary file to S3
        with open(temp_file_path, 'rb') as temp_file_to_upload:
            s3_file_name = "scraped_data/scraped_alberta_1_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")


# # Run the scraping function
# asyncio.run(scrape_alberta_site_1())

