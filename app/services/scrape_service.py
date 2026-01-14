from fastapi import HTTPException,status
# from app.core.security import decode_access_token
from app.utils.site_type_detector import is_dynamic_site
from urllib.parse import urljoin, urlparse
import re
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from app.utils.robot_parser import is_scraping_allowed


RELEVANT_KEYWORDS = [
    "about", "about-us", "who-we-are", "our-story", "history",
    "mission", "vision", "values", "philosophy", "principles",
    "leadership", "management", "team", "board", "founders",
    "careers", "career", "jobs", "join-us", "openings", "hiring",
    "work-with-us", "culture", "life-at", "diversity", "inclusion",
    "press", "media", "news", "announcements",
    "investors", "investor-relations", "financials",
    "contact", "contact-us", "reach-us", "get-in-touch", "support",
    "faq", "help-center", "help"
]


def find_type(url: str, token: str) -> bool:
    if not url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty or whitespace.")

    payload = decode_access_token(token)
    if not payload.get("sub") or not payload.get("id"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could Not Validate User")

    return is_dynamic_site(url)


def extract_internal_links(soup, base_url, keywords) -> set:
    domain = urlparse(base_url).netloc
    internal_links = set()

    for link in soup.find_all("a", href=True):
        full_link = urljoin(base_url, link['href'])
        parsed_link = urlparse(full_link)

        if parsed_link.netloc == domain and any(kw in full_link.lower() for kw in keywords):
            internal_links.add(full_link)

    return internal_links


def beautiful_scrape(url: str) -> dict:
    if not is_scraping_allowed(url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt")

    result = {}
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        internal_links = extract_internal_links(soup, url, RELEVANT_KEYWORDS)

        for link in internal_links:
            try:
                page_response = requests.get(link, timeout=10)
                page_response.raise_for_status()
                page_soup = BeautifulSoup(page_response.text, "html.parser")

                for tag in page_soup(["script", "style", "noscript"]):
                    tag.extract()

                text = re.sub(r'\s+', ' ', page_soup.get_text()).strip()
                page_name = urlparse(link).path.strip("/").replace("/", "-") or "home"
                result[page_name] = text
            except Exception as e:
                print(f"[ERROR] Failed to scrape {link}: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to scrape homepage {url}: {e}")

    return result


async def playwright_scrape(url: str) -> dict:
    if not is_scraping_allowed(url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt")

    result = {}
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                java_script_enabled=True,
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Referer": url
                }
            )
            page = await context.new_page()

            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle")
            await page.wait_for_selector("body", timeout=5000)
            await page.wait_for_timeout(3000)

            domain = urlparse(url).netloc
            links = await page.eval_on_selector_all('a[href]', "elements => elements.map(e => e.href)")

            internal_links = {
                link for link in links
                if urlparse(link).netloc == domain and any(kw in link.lower() for kw in RELEVANT_KEYWORDS)
            }

            if not internal_links:
                text = await page.evaluate("document.body.innerText")
                result["home"] = re.sub(r'\s+', ' ', text).strip()
                return result

            successful_scrapes = 0
            for link in internal_links:
                try:
                    await page.goto(link, timeout=20000)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_selector("body", timeout=5000)
                    await page.wait_for_timeout(2000)

                    text = await page.evaluate("document.body.innerText")
                    page_name = urlparse(link).path.strip("/").replace("/", "-") or "home"
                    result[page_name] = re.sub(r'\s+', ' ', text).strip()
                    successful_scrapes += 1
                except Exception as e:
                    print(f"[ERROR] Failed to scrape {link}: {e}")

            await browser.close()

            if successful_scrapes == 0:
                raise HTTPException(
                    status_code=403,
                    detail="Scraping blocked by the server. robots.txt allows it, but access was denied."
                )

    except Exception as e:
        print(f"[ERROR] Playwright failed on {url}: {e}")

    return result


async def get_scraped_data(url: str, token: str):
    return await playwright_scrape(url) if find_type(url, token) else beautiful_scrape(url)