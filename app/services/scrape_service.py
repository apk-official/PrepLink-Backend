import asyncio
import time

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

# -----------------------------
# Added: Safety + Politeness
# -----------------------------
MAX_PAGES = 10
POLITENESS_DELAY_SEC = 1.0
MAX_CHARS_PER_PAGE = 20_000
MAX_TOTAL_CHARS = 100_000

BACKOFF_BASE_SEC = 2.0
BACKOFF_MAX_RETRIES = 2

DEFAULT_HEADERS = {
    "User-Agent": "PrepLinkBot/0.1 (+https://github.com/apk-official/PrepLinkApp)"
}

def find_type(url: str, token: str) -> bool:
    if not url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty or whitespace.")
    return is_dynamic_site(url)


def extract_internal_links(soup, base_url, keywords) -> list:
    domain = urlparse(base_url).netloc
    links = []

    for link in soup.find_all("a", href=True):
        full_link = urljoin(base_url, link["href"])
        parsed_link = urlparse(full_link)

        if parsed_link.scheme not in ("http", "https"):
            continue

        if parsed_link.netloc == domain and any(kw in full_link.lower() for kw in keywords):
            links.append(full_link)

    # de-dup while preserving order
    seen = set()
    deduped = []
    for l in links:
        if l not in seen:
            seen.add(l)
            deduped.append(l)

    return deduped


def beautiful_scrape(url: str) -> dict:
    if not is_scraping_allowed(url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt")

    result = {"base_url": url, "pages": []}
    total_chars = 0
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        internal_links = extract_internal_links(soup, url, RELEVANT_KEYWORDS)
        internal_links = internal_links[:MAX_PAGES]

        # If no internal links, return homepage text (with caps)
        if not internal_links:
            for tag in soup(["script", "style", "noscript"]):
                tag.extract()
            text = re.sub(r"\s+", " ", soup.get_text()).strip()
            text = text[:MAX_CHARS_PER_PAGE]

            result["pages"].append({"key": "home", "url": url, "text": text})
            return result

        for link in internal_links:
            # Step (3): per-link robots check
            if not is_scraping_allowed(link):
                continue

            # Step (2): politeness delay
            time.sleep(POLITENESS_DELAY_SEC)
            try:
                page_response = requests.get(link, timeout=10)
                page_response.raise_for_status()
                page_soup = BeautifulSoup(page_response.text, "html.parser")

                for tag in page_soup(["script", "style", "noscript"]):
                    tag.extract()

                text = re.sub(r'\s+', ' ', page_soup.get_text()).strip()
                text = text[:MAX_CHARS_PER_PAGE]
                page_name = urlparse(link).path.strip("/").replace("/", "-") or "home"
                result["pages"].append({"key":page_name,"url":link,"text":text})
                total_chars += len(text)
                # Step (4): cap total
                if total_chars >= MAX_TOTAL_CHARS:
                    break
            except Exception as e:
                print(f"[ERROR] Failed to scrape {link}: {e}")


    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to scrape homepage {url}: {e}")

    return result


async def playwright_scrape(url: str) -> dict:
    if not is_scraping_allowed(url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt")

    result = {"base_url": url, "pages": []}
    total_chars = 0

    async def _goto_with_backoff(page, target_url: str, timeout_ms: int):
        """
        Step (5) for Playwright: retry with backoff on navigation errors.
        """
        for attempt in range(BACKOFF_MAX_RETRIES + 1):
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
                await page.wait_for_selector("body", timeout=5000)
                return
            except Exception:
                if attempt == BACKOFF_MAX_RETRIES:
                    raise
                await asyncio.sleep(BACKOFF_BASE_SEC * (2 ** attempt))

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
                if urlparse(link).netloc == domain and any(kw in urlparse(link).path.lower() for kw in RELEVANT_KEYWORDS)
            }
            # de-dup while preserving order
            seen = set()
            deduped = []
            for l in internal_links:
                if l not in seen:
                    seen.add(l)
                    deduped.append(l)

            deduped = deduped[:MAX_PAGES]

            if not deduped:
                text = await page.evaluate("document.body.innerText")
                text = re.sub(r"\s+", " ", text).strip()
                text = text[:MAX_CHARS_PER_PAGE]

                result["pages"].append({"key": "home", "url": url, "text": text})
                await browser.close()
                return result

            successful_scrapes = 0

            for link in deduped:
                # Step (3): per-link robots check
                if not is_scraping_allowed(link):
                    continue

                # Step (2): politeness delay
                await asyncio.sleep(POLITENESS_DELAY_SEC)

                try:
                    await _goto_with_backoff(page, link, timeout_ms=20000)
                    await asyncio.sleep(0.8)

                    text = await page.evaluate("document.body.innerText")
                    text = re.sub(r"\s+", " ", text).strip()

                    # Step (4): cap per page
                    text = text[:MAX_CHARS_PER_PAGE]

                    page_name = urlparse(link).path.strip("/").replace("/", "-") or "home"
                    result["pages"].append({"key": page_name, "url": link, "text": text})

                    successful_scrapes += 1
                    total_chars += len(text)

                    # Step (4): cap total
                    if total_chars >= MAX_TOTAL_CHARS:
                        break

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