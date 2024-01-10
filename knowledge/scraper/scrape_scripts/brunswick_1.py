import asyncio
import tempfile

from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from playwright.async_api import async_playwright

from chatbackend.configs.logging_config import configure_logger
from knowledge.scraper.scraper_utils import download_pdf, sanitize_filename

logger = configure_logger(__name__)

# Base URL
base_url = "https://www.nanb.nb.ca/"

async def extract_nav_links(page):
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('.nav-menu .menu-links > li > a').forEach(a => {
            if (a.offsetParent !== null) {
                links.push({text: a.innerText.trim(), href: a.href});
            }
        });
        return links;
    }''')

async def extract_page_links(page):
    return await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            if (a.href && !a.href.startsWith('javascript') && a.offsetParent !== null) {
                links.push(a.href);
            }
        });
        return links.filter(href => href.startsWith(document.location.origin));
    }''')

async def scrape_html_content(page, url):
    try:
        await page.goto(url, timeout=60000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        main_content = soup.find('main')
        content_text = ""

        if main_content:
            subelements = main_content.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'a'])
            for subelement in subelements:
                if subelement.name == 'a' and 'href' in subelement.attrs:
                    if subelement['href'].endswith('.pdf'):
                        pdf_url = subelement['href']
                        pdf_name = sanitize_filename(subelement.get_text(strip=True)) + '.pdf'
                        await download_pdf(pdf_url, pdf_name)
                    else:
                        content_text += f"{subelement.get_text(strip=True)}\n\n"
                else:
                    content_text += f"{subelement.get_text(strip=True)}\n\n"
        else:
            content_text += "Main content not found.\n"

        return content_text
    except Exception as e:
        logger.error(f"Error scraping content from {url}: {str(e)}")
        return None
    
async def process_page(page, url, temp_file, processed_urls):
    if url in processed_urls or not url.startswith(base_url):
        return
    processed_urls.add(url)

    logger.info(f"Processing page: {url}")
    content = await scrape_html_content(page, url)
    if content:
        temp_file.write(f"URL: {url}\n{content}")
        temp_file.write("------------------------------------------------------------\n\n")

    page_links = await extract_page_links(page)
    for link in page_links:
        await process_page(page, link, temp_file, processed_urls)

async def scrape_nanb_site():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(base_url, timeout=60000)

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
            s3_file_name = "scraped_data/scraped_nanb_content.txt"
            default_storage.save(s3_file_name, ContentFile(temp_file_to_upload.read()))
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

# Run the scraping process
asyncio.run(scrape_nanb_site())