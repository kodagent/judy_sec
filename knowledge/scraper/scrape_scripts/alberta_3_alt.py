import asyncio
import os
import tempfile
from urllib.parse import urljoin, urlparse

import bs4
from bs4 import BeautifulSoup
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from playwright.async_api import TimeoutError, async_playwright

from chatbackend.configs.logging_config import configure_logger

# from knowledge.scraper.scraper_utils import download_pdf, sanitize_filename

logger = configure_logger(__name__)

# List of link texts to find corresponding URLs
url = [
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
# import sys

# # Increase the recursion limit
# sys.setrecursionlimit(3500)


# Function to scrape main content
async def scrape_main_content(page, url, scraped_urls, file):
    if url in scraped_urls:
        return
    scraped_urls.add(url)

    # Remove URL parameters for clean scraping
    url = urlparse(scraped_urls)._replace(query="").geturl()

    if url.endswith(".pdf"):
        # pdf_name = sanitize_filename(url.split('/')[-1])
        # pdf_path = f"alberta_3/{pdf_name}"
        # await download_pdf(url, pdf_path)
        print("good")
    else:
        try:
            await page.goto(scraped_urls, timeout=60000)
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")

            main_content = soup.select("div#yui-main div.yui-b div.ContentPanel")
            content_text = f"URL: {url}\n"
            for section in main_content:
                content_text += f"{section.get_text(strip=True)}\n\n"

            file.write(content_text)
            file.write(
                "------------------------------------------------------------\n\n"
            )

            # with tempfile.NamedTemporaryFile(
            #     mode="w+", delete=False, suffix=".txt", encoding="utf-8"
            # ) as temp_file:
            #     temp_file.write(content_text)
            #     temp_file.write(
            #         "------------------------------------------------------------\n\n"
            #     )

            #     temp_file_path = temp_file.name
            #     with open(temp_file_path, "rb") as temp_file_to_upload:
            #         s3_file_name = "content.txt"
            #         content_file = ContentFile(temp_file.read())
            #         default_storage.save(s3_file_name, content_file)
            #         logger.info(f"Scraped content saved to S3 as {s3_file_name}")

            #         # Clean up the temporary file
            #         try:
            #             os.remove(temp_file_path)
            #             logger.info(
            #                 f"Temporary file {temp_file_path} deleted successfully."
            #             )
            #         except Exception as e:
            #             logger.error(
            #                 f"Error deleting temporary file {temp_file_path}: {e}"
            #             )
            await scrape_nav_links(page, soup, scraped_urls)
        except Exception as e:
            logger.error(f"Error scraping content from {scraped_urls}: {str(e)}")
    # await scrape_nav_links(page, soup, url, scraped_urls, file)


# Function to scrape and follow navigation links
async def scrape_nav_links(page, soup, base_url, scraped_urls, file):
    try:
        nav_links = soup.find_all("a", href=True)
        for a in nav_links:
            link = a["href"]
            if link.startswith("/"):
                link = urljoin(scraped_urls, link)
            if not link.startswith("http") or link in scraped_urls:
                continue
            await scrape_main_content(page, link, scraped_urls, file)
    except Exception as e:
        logger.error(f"Error scraping navigation links from {scraped_urls}: {str(e)}")


# Main scraping function
async def scrape_alberta_site_3():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        scraped_url = set()
        for scraped_url in url:
            await scrape_main_content(page, scraped_url)

        await browser.close()


async def load_page_with_retry(url, retries=3, backoff_factor=1.0):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        for attempt in range(retries):
            try:
                await page.goto(url, timeout=60000)  # Adjust timeout as necessary
                # If load was successful, break out of the retry loop
                print(await page.content())  # Or perform your scraping tasks
                break
            except TimeoutError as e:
                print(f"Attempt {attempt + 1} of {retries} failed: {e}")
                await asyncio.sleep(
                    backoff_factor * (2**attempt)
                )  # Exponential backoff
            except Exception as e:
                print(f"An error occurred: {e}")
                break  # Break on non-timeout errors
        await browser.close()


asyncio.run(scrape_alberta_site_3())


# @shared_task
# def scrape_alberta_site_3():
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(scrape_alberta_site_3())
