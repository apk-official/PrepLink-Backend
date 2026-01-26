# app/services/tos_extractor.py
"""
ToS / Legal Page Extractor

This module is intentionally "vibe-coded":
- It does not try to be perfect or legally authoritative
- It tries to be practical, cautious, and transparent
- The goal is to *discover and extract* Terms / Privacy pages
  so they can be reviewed (by humans or tools) before scraping

Key ideas:
- Always respect robots.txt first
- Prefer lightweight scraping (requests + BeautifulSoup)
- Fall back to Playwright only when necessary
- Limit scope aggressively to avoid aggressive crawling
"""
import re
import time
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import HTTPException
from playwright.async_api import async_playwright

from app.utils.site_type_detector import is_dynamic_site
from app.utils.robot_parser import is_scraping_allowed


TOS_KEYWORDS = [
    "terms", "terms-of-service", "terms-of-use", "terms-and-conditions",
    "privacy", "privacy-policy",
    "legal", "policies", "policy",
    "cookies", "cookie-policy",
]

MAX_TOS_PAGES = 3
POLITENESS_DELAY_SEC = 1.0
MAX_CHARS_PER_PAGE = 40_000

DEFAULT_HEADERS = {
    "User-Agent": "PrepLinkBot/0.1 (+https://github.com/<your-username>/<your-repo>)"
}


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _strip_noise(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.extract()


def _extract_candidate_links_from_html(base_url: str, html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    domain = urlparse(base_url).netloc

    links: List[str] = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        parsed = urlparse(full)

        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc != domain:
            continue

        lower = full.lower()
        if any(k in lower for k in TOS_KEYWORDS):
            links.append(full)

    # de-dup preserve order
    seen = set()
    out = []
    for l in links:
        if l not in seen:
            seen.add(l)
            out.append(l)

    return out


def _guess_common_tos_urls(base_url: str) -> List[str]:
    """
    Fallback guesses if we can't find links on the homepage.
    """
    base = base_url.rstrip("/")
    guesses = [
        f"{base}/terms",
        f"{base}/terms-of-service",
        f"{base}/terms-of-use",
        f"{base}/terms-and-conditions",
        f"{base}/privacy",
        f"{base}/privacy-policy",
        f"{base}/legal",
        f"{base}/policies",
        f"{base}/cookie-policy",
    ]
    # de-dup
    seen = set()
    out = []
    for g in guesses:
        if g not in seen:
            seen.add(g)
            out.append(g)
    return out


def _requests_get(url: str, timeout: int = 10) -> requests.Response:
    resp = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
    resp.raise_for_status()
    return resp


def _bs_extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    _strip_noise(soup)

    # Prefer <main> if present
    main = soup.find("main")
    if main:
        return _clean_text(main.get_text(" "))

    # Else fallback to body text
    body = soup.body
    if body:
        return _clean_text(body.get_text(" "))

    return _clean_text(soup.get_text(" "))


def tos_extract_bs(base_url: str) -> Dict:
    """
    Extract TOS/Privacy-like pages using requests + BeautifulSoup.
    Returns: {"base_url":..., "pages":[{"key":..., "url":..., "text":...}, ...]}
    """
    if not is_scraping_allowed(base_url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt (base URL)")

    result = {"base_url": base_url, "pages": []}

    # 1) fetch homepage
    try:
        home_resp = _requests_get(base_url, timeout=10)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch base URL: {e}")

    # 2) extract candidate TOS links
    candidates = _extract_candidate_links_from_html(base_url, home_resp.text)

    # 3) if none found, try guessing common URLs
    if not candidates:
        candidates = _guess_common_tos_urls(base_url)

    # 4) limit how many we try
    candidates = candidates[:MAX_TOS_PAGES]

    for link in candidates:
        # robots check per path
        if not is_scraping_allowed(link):
            continue

        time.sleep(POLITENESS_DELAY_SEC)

        try:
            resp = _requests_get(link, timeout=10)
            text = _bs_extract_main_text(resp.text)
            text = text[:MAX_CHARS_PER_PAGE]

            key = urlparse(link).path.strip("/").replace("/", "-") or "legal"
            result["pages"].append({"key": key, "url": link, "text": text})
        except Exception:
            continue

    return result


async def tos_extract_playwright(base_url: str) -> Dict:
    """
    Same output format as tos_extract_bs, but uses Playwright.
    Helpful when the site renders legal pages dynamically.
    """
    if not is_scraping_allowed(base_url):
        raise HTTPException(status_code=403, detail="Scraping disallowed by robots.txt (base URL)")

    result = {"base_url": base_url, "pages": []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=DEFAULT_HEADERS["User-Agent"])
        page = await context.new_page()

        await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector("body", timeout=5000)
        await asyncio.sleep(1.0)

        links = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        domain = urlparse(base_url).netloc

        candidates = []
        for l in links:
            if urlparse(l).netloc == domain and any(k in l.lower() for k in TOS_KEYWORDS):
                candidates.append(l)

        # de-dup preserve order
        seen = set()
        deduped = []
        for l in candidates:
            if l not in seen:
                seen.add(l)
                deduped.append(l)

        if not deduped:
            deduped = _guess_common_tos_urls(base_url)

        deduped = deduped[:MAX_TOS_PAGES]

        for link in deduped:
            if not is_scraping_allowed(link):
                continue

            await asyncio.sleep(POLITENESS_DELAY_SEC)

            try:
                await page.goto(link, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_selector("body", timeout=5000)
                await asyncio.sleep(0.5)

                # Prefer main if exists
                has_main = await page.locator("main").count()
                if has_main:
                    text = await page.locator("main").inner_text()
                else:
                    text = await page.evaluate("document.body.innerText")

                text = _clean_text(text)[:MAX_CHARS_PER_PAGE]
                key = urlparse(link).path.strip("/").replace("/", "-") or "legal"
                result["pages"].append({"key": key, "url": link, "text": text})
            except Exception:
                continue

        await browser.close()

    return result


async def get_tos_data(base_url: str) -> Dict:
    """
    Picks best method automatically.
    """
    try:
        if is_dynamic_site(base_url):
            return await tos_extract_playwright(base_url)
        return tos_extract_bs(base_url)
    except Exception:
        # fallback
        return await tos_extract_playwright(base_url)
