import random
import re
import sys
import time
import json
import urllib.parse
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup

_http_session = requests.Session()
_http_session.headers.update(
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
)

# Simple search result cache (avoids repeated queries)
_search_cache = OrderedDict()
_cache_max_size = 50
_cache_ttl_seconds = 600  # 10 minutes


def _get_cached(query: str):
    """Get cached result if fresh."""
    key = query.lower().strip()
    if key in _search_cache:
        result, timestamp = _search_cache[key]
        if time.time() - timestamp < _cache_ttl_seconds:
            return result
        del _search_cache[key]
    return None


def _cache_result(query: str, result: str):
    """Cache a search result."""
    key = query.lower().strip()
    _search_cache[key] = (result, time.time())
    while len(_search_cache) > _cache_max_size:
        _search_cache.popitem(last=False)


def internet_research(query: str):
    """Run internet research with multiple lightweight fallbacks. Caches results."""
    if not query or not query.strip():
        return "Sir, the search query appears to be empty."

    # Check cache first
    cached = _get_cached(query)
    if cached:
        return cached

    result = _do_search(query)
    _cache_result(query, result)
    return result


def _do_search(query: str) -> str:
    """Actual search implementation with prioritized providers."""
    
    # 1. Try DuckDuckGo via ddgs (Fastest and usually cleanest)
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            if results:
                output = [f"I found the following information for '{query}':"]
                for i, r in enumerate(results, start=1):
                    title = r.get('title')
                    body = r.get('body', '').strip()
                    link = r.get('href')
                    output.append(f"{i}. {title}\n   {body}\n   🔗 {link}")
                return "\n".join(output)
    except Exception as e:
        print(f"[search] DDGS failed: {e}", file=sys.stderr)

    # 2. Try Google Search fallback
    try:
        from googlesearch import search
        results = list(search(query, num_results=5, lang="ru" if any(ord(c) > 127 for c in query) else "en"))
        if results:
            output = [f"Google results for '{query}':"]
            for i, url in enumerate(results[:3], start=1):
                try:
                    # Try to fetch snippet from page
                    resp = _http_session.get(url, timeout=4)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        title = (soup.title.string if soup.title else url).strip()
                        # Extract first meaningful paragraphs
                        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 30]
                        snippet = " ".join(paragraphs[:2])
                        if len(snippet) > 400: snippet = snippet[:400] + "..."
                        output.append(f"{i}. {title}\n   {snippet or 'No snippet available'}\n   🔗 {url}")
                    else:
                        output.append(f"{i}. {url}\n   (Page could not be previewed)")
                except Exception:
                    output.append(f"{i}. {url}")
            return "\n".join(output)
    except Exception as e:
        print(f"[search] Google failed: {e}", file=sys.stderr)

    # 3. Wikipedia Fallback
    wiki = _try_wikipedia(query)
    if wiki:
        return wiki

    return f"I'm sorry Sir, I was unable to retrieve any search results for '{query}' at the moment."


def _try_wikipedia(query: str) -> str:
    """Try Wikipedia API with language detection."""
    lang = "ru" if any(ord(c) > 127 for c in query) else "en"
    try:
        encoded = urllib.parse.quote(query.replace(' ', '_'))
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        response = _http_session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "extract" in data:
                return f"According to Wikipedia [{lang}]:\n{data['extract']}\n🔗 {data['content_urls']['desktop']['page']}"
    except Exception:
        pass
    return ""


def get_news(city: str):
    """Return a brief latest-news summary for a city."""
    if not city: return "Sir, please specify a city for the news."
    return internet_research(f"latest news in {city} today")


def get_weather(city: str):
    """Return current weather from wttr.in."""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t+humidity:+%h+wind:+%w"
        response = _http_session.get(url, timeout=8)
        if response.status_code == 200 and response.text.strip():
            return f"The current weather in {city} is {response.text.strip()}."
    except Exception:
        pass
    return f"I was unable to retrieve the weather for {city} Sir."


def manage_web(action: str, query: str = "", city: str = ""):
    """Bridge for model tool calling."""
    if action == "internet_research": return internet_research(query)
    elif action == "get_news": return get_news(city)
    elif action == "get_weather": return get_weather(city)
    return "Unknown web action."


def register_plugin():
    return [manage_web], {"manage_web": manage_web}
