import asyncio
import os
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from chatbackend.configs.logging_config import configure_logger

logger = configure_logger(__name__)

# Base URL of the website
base_url = "https://www.cno.org/en/"

# Directory to save PDFs
pdf_dir = "knowledge/scraper/downloaded_pdfs"
os.makedirs(pdf_dir, exist_ok=True)

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

# Function to sanitize file names
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '-', name)

# Function to download PDF using Playwright
async def download_pdf(page, url, pdf_name):
    try:
        # Initiate download
        download = await page.wait_for_download(lambda: page.goto(url))
        await download.save_as(pdf_name)
        logger.info(f"PDF downloaded from {url}")
        return True
    except Exception as e:
        logger.error(f"Error downloading PDF from {url}: {str(e)}")
        return False
    
# Async function to get content using Playwright
async def scrape_html_content(page, url):
    try:
        await page.goto(url)
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
    await page.goto(url)
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
        pdf_name = os.path.join(pdf_dir, f"{sanitize_filename(title)}.pdf")
        if await download_pdf(page, category_url, pdf_name):
            logger.info(f"Downloaded PDF: {category_url}")
        else:
            logger.error(f"Failed to download PDF: {category_url}")
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

        await page.goto(base_url)
        main_links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({text: a.innerText, href: a.href}))
        }''')

        with open("knowledge/scraper/scraped_data/scraped_ontario_content.txt", "w", encoding="utf-8") as file:
            for link in main_links:
                if link['text'].strip() in link_texts_to_find:
                    absolute_url = urljoin(base_url, link['href'])
                    await process_category(page, absolute_url, file, processed_urls)

        await browser.close()
        logger.info("Scraping completed.")

# asyncio.run(scrape_ontario_site())
