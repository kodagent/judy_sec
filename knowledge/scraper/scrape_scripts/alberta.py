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
async def scrape_main_content(page, url):
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        main_content = soup.find_all('div', class_='row')

        content_text = ""
        for content_div in main_content:
            title = content_div.find('h4', class_='title')
            if title:
                content_text += f"Title: {title.get_text(strip=True)}\n\n"
            paragraphs = content_div.find_all('p')
            for paragraph in paragraphs:
                content_text += f"{paragraph.get_text(strip=True)}\n\n"

        return content_text
    except Exception as e:
        print(f"Error scraping content from {url}: {str(e)}")
        return None

# Function to scrape navigation links
async def scrape_nav_links(page, url):
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        nav_links_div = soup.find_all('div', class_='row row-cols-1 row-cols-md-3 g-4 pt-3')

        links = []
        for div in nav_links_div:
            a_tags = div.find_all('a')
            for a in a_tags:
                link = a['href']
                title = a.find('h5', class_='card-title')
                if title:
                    links.append((title.get_text(strip=True), link))

        return links
    except Exception as e:
        print(f"Error scraping navigation links from {url}: {str(e)}")
        return []

# Main scraping function to handle multiple URLs
async def scrape_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        for url in urls_to_scrape:
            main_content = await scrape_main_content(page, url)
            nav_links = await scrape_nav_links(page, url)

            logger.info(f"Main Content for {url}:\n{main_content}")
            logger.info(f"Navigation Links for {url}:\n{nav_links}")

        await browser.close()


# Replace 'base_url' with the actual URL of the site you're scraping
# asyncio.run(scrape_site(base_url))
