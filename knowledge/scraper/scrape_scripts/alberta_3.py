import asyncio
import os
import tempfile
from urllib.parse import urljoin, urlparse

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
    "https://www.crpna.ab.ca/CRPNAMember/Home/CRPNAMember/Home_Page.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/About/About_CRPNA/CRPNAMember/Home_Page_New/About_CRPNA.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/About/CRPNA_Council/CRPNAMember/Home_Page_New/CRPNA_Council.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/About/About_RPNs/CRPNAMember/Home_Page_New/About_RPNs.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/Find_a_RPN/CRPNAMember/Contact_Management/Directory.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/CRPNA_Members/CRPNAMember/CRPNA_Member/CRPNA_Members.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/Complaints___Concerns/CRPNAMember/Complaints_Concerns/Complaints_Concerns.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/Complaints_Concerns/Sexual_Abuse_and_Sexual_Misconduct_Patient_Complaints/Sexual_Abuse_and_Sexual_Misconduct_Complaints.aspx",
    "https://www.crpna.ab.ca/CRPNAMember/Library/CRPNAMember/Library/Library.aspxhttps://www.crpna.ab.ca/CRPNAMember/Contact_Us/CRPNAMember/Home_Page_New/Contact_Us.aspx",
]


# Function to scrape main content
async def scrape_main_content(page, url, scraped_urls, file):
    if url in scraped_urls:
        return
    scraped_urls.add(url)

    # Remove URL parameters for clean scraping
    url = urlparse(url)._replace(query="").geturl()

    if url.endswith(".pdf"):
        pdf_name = sanitize_filename(url.split("/")[-1])
        pdf_path = f"alberta_3/{pdf_name}"
        await download_pdf(url, pdf_path)
    else:
        try:
            await page.goto(url, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            main_content = soup.select("#yui-main div.yui-b div.ContentPanel")
            content_text = f"URL: {url}\n"
            for section in main_content:
                content_text += f"{section.get_text(strip=True)}\n\n"

            file.write(content_text)
            file.write(
                "------------------------------------------------------------\n\n"
            )

            await scrape_nav_links(page, soup, url, scraped_urls, file)
        except Exception as e:
            logger.error(f"Error scraping content from {url}: {str(e)}")
    # await scrape_nav_links(page, soup, url, scraped_urls, file)


# Function to scrape and follow navigation links
async def scrape_nav_links(page, soup, base_url, scraped_urls, file):
    try:
        nav_links = soup.find_all("a", href=True)
        for a in nav_links:
            link = a["href"]
            if link.startswith("/"):
                link = urljoin(base_url, link)
            if not link.startswith("http") or link in scraped_urls:
                continue
            await scrape_main_content(page, link, scraped_urls, file)
    except Exception as e:
        logger.error(f"Error scraping navigation links from {base_url}: {str(e)}")


# Main scraping function
async def scrape_alberta_site_3():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        scraped_urls = set()
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".txt", encoding="utf-8"
        ) as temp_file:
            for base_url in urls_to_scrape:
                await scrape_main_content(page, base_url, scraped_urls, temp_file)

            temp_file_path = temp_file.name

        await browser.close()

        with open(temp_file_path, "rb") as temp_file_to_upload:
            s3_file_name = "scraped_data/alberta_3/scraped_alberta_3_content.txt"
            content_file = ContentFile(temp_file_to_upload.read())
            default_storage.save(s3_file_name, content_file)
            logger.info(f"Scraped content saved to S3 as {s3_file_name}")

        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
            logger.info(f"Temporary file {temp_file_path} deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting temporary file {temp_file_path}: {e}")


# # Run the scraping function
# asyncio.run(scrape_alberta_site_3())

# @shared_task
# def scrape_alberta_site_3():
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(scrape_alberta_site_3())
