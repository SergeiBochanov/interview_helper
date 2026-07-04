import trafilatura

def extract_text_from_url(url: str) -> str:
    """
    Скачивает веб-страницу по ссылке и извлекает из неё чистый текст.
    """
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        raise ValueError(f"Не удалось скачать контент по ссылке: {url}")
        
    clean_text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
    if not clean_text:
        raise ValueError("Не удалось извлечь полезный текст из страницы.")
        
    return clean_text