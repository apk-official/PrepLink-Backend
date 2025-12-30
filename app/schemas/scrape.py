from pydantic import BaseModel, HttpUrl, Field

class ScrapeRequest(BaseModel):
    """
        Request body schema for web scraping.

        Attributes:
            url (HttpUrl): The target website URL to scrape.
        """
    url: HttpUrl = Field(..., description="Valid URL to scrape", examples=["https://example.com"])

    # model_config structure suggested via ChatGPT for Pydantic v2 compatibility
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com"
                }
            ]
        }
    }