import requests
from bs4 import BeautifulSoup

def is_dynamic_site(url:str)->bool:
    """
        Check whether the given website is static or dynamic.

        Logic behind this:
        If the site doesn't have much visible text or has too many <script> tags, assume dynamic.
        If common JS frontend frameworks like React, Vue, or Angular found in scripts, mark as dynamic.
        If request itself fails, just assume it's dynamic to avoid breaking things.

        Args:
            url (str): Full website URL.

        Returns:
            bool:
                True  -> Dynamic site (uses JS frameworks, API calls, etc.)
                False -> Static site (simple HTML-based)
        """
    try:
        response = requests.get(url,timeout=10)
        response.raise_for_status()


        soup = BeautifulSoup(response.text,"html.parser")

        # If there's very little visible content or too much JS
        body_text = soup.body.get_text(strip=True)
        scripts = soup.find_all("script")

        if len(body_text)<100 or len(scripts)>20:
            return True #Likely Dynamic

        for script in scripts:
            src = script.get("src", "")
            if any(lib in src for lib in ["react", "vue", "angular"]):
                return True

        return False
    except Exception as e:
        print(f"[ERROR] Failed to analyse {url}: {e}")
        return True #Return Dynamic