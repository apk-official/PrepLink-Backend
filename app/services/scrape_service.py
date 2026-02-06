# app/services/scrape_service.py
import asyncio
import os
import re
import time
import hashlib
from typing import Optional, Tuple, Dict, Any, List

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException, status
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

from app.utils.site_type_detector import is_dynamic_site
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
    "faq", "help-center", "help",
]

# -----------------------------
# Safety + Politeness
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


# ============================================================
# Helper functions
# ============================================================

def normalise_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def extract_home_title_from_soup(soup: BeautifulSoup) -> Optional[str]:
    t = soup.find("title")
    return t.get_text(strip=True) if t else None


def normalise_company_name_from_title(title: Optional[str]) -> Optional[str]:
    """
    Convert a <title> into a decent company name.

    Fix for your issue:
    - Old logic used `min(parts, key=len)` which often returns "Home"
    - New logic prefers the FIRST meaningful segment, and ignores page-ish words.

    Examples:
      "De'Lead | Home" -> "De'Lead"
      "De'Lead International | About Us" -> "De'Lead International"
      "Acme - About" -> "Acme"
    """
    if not title:
        return None

    t = normalise_whitespace(title)

    # split on common title separators
    parts = re.split(r"\s*[\|\-•·:–—]\s*", t)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return t

    page_words = {
        "home", "about", "about us", "contact", "contact us", "login", "sign in",
        "terms", "terms of service", "terms of use", "privacy", "privacy policy"
    }

    # Prefer the first part unless it's clearly a page word
    first = parts[0]
    if first.lower() not in page_words:
        cleaned = re.sub(r"\b(home|official website)\b", "", first, flags=re.I).strip()
        return cleaned or first

    # Otherwise, return the first part that is not a page word
    for p in parts:
        if p.lower() not in page_words:
            cleaned = re.sub(r"\b(home|official website)\b", "", p, flags=re.I).strip()
            return cleaned or p

    # Fallback: original full title
    return t


def _rel_tokens(rel_val) -> List[str]:
    """
    BeautifulSoup rel can be None / str / list[str].
    Convert to a list of lower tokens.
    """
    if not rel_val:
        return []
    if isinstance(rel_val, list):
        return [str(x).lower().strip() for x in rel_val if str(x).strip()]
    return [str(rel_val).lower().strip()]


def extract_favicon_url_from_html(base_url: str, html: str) -> str:
    """
    Try to find favicon via <link rel="icon"...>. Fallback to /favicon.ico.
    More robust than strict-equality rel checks.
    """
    soup = BeautifulSoup(html, "html.parser")
    icon_tokens = {"icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed"}

    for link in soup.find_all("link", href=True):
        rel_tokens = _rel_tokens(link.get("rel"))
        rel_joined = " ".join(rel_tokens)

        # match any of the common icon rel types
        if any(tok in rel_joined for tok in icon_tokens):
            return urljoin(base_url, link["href"])

    return urljoin(base_url, "/favicon.ico")


def download_favicon(
    favicon_url: str,
    company_id: int,
    save_dir: str = "static/favicons",
) -> Tuple[Optional[str], Optional[str]]:
    """
    Download favicon to local filesystem and return (favicon_url, local_path).
    If download fails, returns (None, None).
    """
    os.makedirs(save_dir, exist_ok=True)

    try:
        r = requests.get(
            favicon_url,
            timeout=10,
            stream=True,
            headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]},
            allow_redirects=True,
        )
        if r.status_code != 200:
            return None, None

        content = r.content
        if not content or len(content) < 50:
            return None, None

        ctype = (r.headers.get("content-type") or "").lower()
        ext = ".ico"
        if "png" in ctype:
            ext = ".png"
        elif "svg" in ctype:
            ext = ".svg"
        elif "jpeg" in ctype or "jpg" in ctype:
            ext = ".jpg"

        digest = hashlib.sha256(content).hexdigest()[:12]
        filename = f"company_{company_id}_{digest}{ext}"
        path = os.path.join(save_dir, filename)

        with open(path, "wb") as f:
            f.write(content)

        return favicon_url, path

    except Exception:
        return None, None


def extract_internal_links(soup: BeautifulSoup, base_url: str, keywords: List[str]) -> List[str]:
    domain = urlparse(base_url).netloc
    links: List[str] = []

    for a in soup.find_all("a", href=True):
        full_link = urljoin(base_url, a["href"])
        parsed = urlparse(full_link)

        if parsed.scheme not in ("http", "https"):
            continue

        if parsed.netloc == domain and any(kw in full_link.lower() for kw in keywords):
            links.append(full_link)

    # de-dup preserving order
    seen = set()
    deduped: List[str] = []
    for l in links:
        if l not in seen:
            seen.add(l)
            deduped.append(l)

    return deduped


def find_type(url: str) -> bool:
    if not url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL cannot be empty or whitespace.",
        )
    return is_dynamic_site(url)


# ============================================================
# Scrapers
# - Always include homepage
# - Also return:
#   - home_title
#   - favicon_url
#   - company_name_guess (cleaned, not "Home")
# ============================================================

def beautiful_scrape(url: str) -> Dict[str, Any]:
    if not is_scraping_allowed(url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt")

    result: Dict[str, Any] = {
        "base_url": url,
        "home_title": None,
        "company_name_guess": None,
        "favicon_url": None,
        "pages": [],
    }
    total_chars = 0

    try:
        response = requests.get(url, timeout=10, headers=DEFAULT_HEADERS)
        response.raise_for_status()

        # Extract favicon + title before stripping tags
        result["favicon_url"] = extract_favicon_url_from_html(url, response.text)

        soup = BeautifulSoup(response.text, "html.parser")
        home_title = extract_home_title_from_soup(soup)
        result["home_title"] = home_title
        result["company_name_guess"] = normalise_company_name_from_title(home_title)

        # Homepage text
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()

        home_text = normalise_whitespace(soup.get_text())[:MAX_CHARS_PER_PAGE]
        result["pages"].append({"key": "home", "url": url, "text": home_text})
        total_chars += len(home_text)

        if total_chars >= MAX_TOTAL_CHARS:
            return result

        # Internal links (use the cleaned soup; link tags remain)
        internal_links = extract_internal_links(soup, url, RELEVANT_KEYWORDS)[:MAX_PAGES]

        for link in internal_links:
            if total_chars >= MAX_TOTAL_CHARS:
                break
            if not is_scraping_allowed(link):
                continue

            time.sleep(POLITENESS_DELAY_SEC)

            try:
                page_response = requests.get(link, timeout=10, headers=DEFAULT_HEADERS)
                page_response.raise_for_status()

                page_soup = BeautifulSoup(page_response.text, "html.parser")
                for tag in page_soup(["script", "style", "noscript"]):
                    tag.extract()

                text = normalise_whitespace(page_soup.get_text())[:MAX_CHARS_PER_PAGE]
                page_name = urlparse(link).path.strip("/").replace("/", "-") or "page"
                result["pages"].append({"key": page_name, "url": link, "text": text})
                total_chars += len(text)

            except Exception as e:
                print(f"[ERROR] Failed to scrape {link}: {e}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to scrape homepage {url}: {e}")

    return result


async def playwright_scrape(url: str) -> Dict[str, Any]:
    if not is_scraping_allowed(url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt")

    result: Dict[str, Any] = {
        "base_url": url,
        "home_title": None,
        "company_name_guess": None,
        "favicon_url": None,
        "pages": [],
    }
    total_chars = 0

    async def _goto_with_backoff(pw_page, target_url: str, timeout_ms: int) -> None:
        for attempt in range(BACKOFF_MAX_RETRIES + 1):
            try:
                await pw_page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
                await pw_page.wait_for_selector("body", timeout=5000)
                return
            except Exception:
                if attempt == BACKOFF_MAX_RETRIES:
                    raise
                await asyncio.sleep(BACKOFF_BASE_SEC * (2 ** attempt))

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                java_script_enabled=True,
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Referer": url,
                },
            )
            pw_page = await context.new_page()

            # ---------- Load homepage ----------
            await pw_page.goto(url, timeout=30000)
            await pw_page.wait_for_load_state("networkidle")
            await pw_page.wait_for_selector("body", timeout=5000)
            await pw_page.wait_for_timeout(1200)

            # Title + company name guess
            home_title = await pw_page.title()
            result["home_title"] = home_title
            result["company_name_guess"] = normalise_company_name_from_title(home_title)

            # Favicon URL (robust: eval and handle missing selector)
            favicon_href = await pw_page.evaluate(
                """
                () => {
                  const el =
                    document.querySelector("link[rel~='icon']") ||
                    document.querySelector("link[rel='shortcut icon']") ||
                    document.querySelector("link[rel='apple-touch-icon']") ||
                    document.querySelector("link[rel='apple-touch-icon-precomposed']");
                  return el ? el.href : null;
                }
                """
            )
            result["favicon_url"] = favicon_href or urljoin(url, "/favicon.ico")

            # Homepage text
            home_text = await pw_page.evaluate("document.body.innerText")
            home_text = normalise_whitespace(home_text)[:MAX_CHARS_PER_PAGE]
            result["pages"].append({"key": "home", "url": url, "text": home_text})
            total_chars += len(home_text)

            if total_chars >= MAX_TOTAL_CHARS:
                await browser.close()
                return result

            # ---------- Collect internal links ----------
            domain = urlparse(url).netloc
            links = await pw_page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")

            candidates = [
                link for link in links
                if urlparse(link).netloc == domain
                and any(kw in urlparse(link).path.lower() for kw in RELEVANT_KEYWORDS)
            ]

            # de-dup preserving order
            seen = set()
            deduped: List[str] = []
            for l in candidates:
                if l not in seen:
                    seen.add(l)
                    deduped.append(l)

            deduped = deduped[:MAX_PAGES]

            if not deduped:
                await browser.close()
                return result

            successful_scrapes = 0

            # ---------- Scrape internal pages ----------
            for link in deduped:
                if total_chars >= MAX_TOTAL_CHARS:
                    break
                if not is_scraping_allowed(link):
                    continue

                await asyncio.sleep(POLITENESS_DELAY_SEC)

                try:
                    await _goto_with_backoff(pw_page, link, timeout_ms=20000)
                    await asyncio.sleep(0.6)

                    text = await pw_page.evaluate("document.body.innerText")
                    text = normalise_whitespace(text)[:MAX_CHARS_PER_PAGE]

                    page_name = urlparse(link).path.strip("/").replace("/", "-") or "page"
                    result["pages"].append({"key": page_name, "url": link, "text": text})

                    successful_scrapes += 1
                    total_chars += len(text)

                except Exception as e:
                    print(f"[ERROR] Failed to scrape {link}: {e}")

            await browser.close()

            if successful_scrapes == 0:
                raise HTTPException(
                    status_code=403,
                    detail="Scraping blocked by the server. robots.txt allows it, but access was denied.",
                )

    except Exception as e:
        print(f"[ERROR] Playwright failed on {url}: {e}")

    return result


async def get_scraped_data(url: str) -> Dict[str, Any]:
    return await playwright_scrape(url) if find_type(url) else beautiful_scrape(url)
