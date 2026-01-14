import urllib.robotparser
from urllib.parse import urlparse

def is_scraping_allowed(url: str, user_agent: str = "*") -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(user_agent, url)
        print(f"[INFO] robots.txt check for {url}: {allowed}")
        return allowed
    except Exception as e:
        print(f"[WARN] Could not read robots.txt at {robots_url}: {e}")
        return True  # Be cautious: If robots.txt fails, allow by default