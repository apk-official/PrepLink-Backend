def company_page_to_dict(p) -> dict:
    return {
        "page_title": p.page_title,
        "page_url": p.page_url,
        "page_content": p.page_content,
    }
