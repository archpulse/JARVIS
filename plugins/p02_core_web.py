import random
import re
import sys
import time
import json
import urllib.parse
import concurrent.futures
from collections import OrderedDict

import requests
import jarvis_config as cfg

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_http_session = requests.Session()
_http_session.headers.update(
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
)

# Simple search result cache (avoids repeated queries)
_search_cache = OrderedDict()
_cache_max_size = cfg.web_research_cache_size()
_cache_ttl_seconds = cfg.web_research_cache_ttl_seconds()
_cache_enabled = cfg.env_bool("JARVIS_WEB_RESEARCH_CACHE_ENABLED", True)
DDG_RESULT_LIMIT = cfg.env_int("JARVIS_DDG_RESULT_LIMIT", 10)
GOOGLE_RESULT_LIMIT = cfg.env_int("JARVIS_GOOGLE_RESULT_LIMIT", 5)
WEB_RESEARCH_DISPLAY_LIMIT = cfg.env_int("JARVIS_WEB_RESEARCH_DISPLAY_LIMIT", 6)
WEB_RESEARCH_SCRAPE_LIMIT = cfg.env_int("JARVIS_WEB_RESEARCH_SCRAPE_LIMIT", 2)


def _get_cached(query: str):
    """Get cached result if fresh."""
    if not _cache_enabled:
        return None
    key = query.lower().strip()
    if key in _search_cache:
        result, timestamp = _search_cache[key]
        if time.time() - timestamp < _cache_ttl_seconds:
            return result
        del _search_cache[key]
    return None


def _cache_result(query: str, result: str):
    """Cache a search result."""
    if not _cache_enabled:
        return
    key = query.lower().strip()
    _search_cache[key] = (result, time.time())
    while len(_search_cache) > _cache_max_size:
        _search_cache.popitem(last=False)


def _fetch_page_content(url: str, timeout: int = 7) -> str:
    """Fetch and extract clean text from a URL."""
    try:
        resp = _http_session.get(url, timeout=timeout)
        if resp.status_code == 200:
            if BeautifulSoup is None:
                text = " ".join(resp.text.split())
                return text[:2000] + "..." if len(text) > 2000 else text
            soup = BeautifulSoup(resp.text, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                element.decompose()
            text = soup.get_text(separator=' ')
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if len(chunk) > 20)
            return text[:2000] + "..." if len(text) > 2000 else text
    except Exception:
        pass
    return ""


def _try_wikipedia(query: str) -> str:
    """Try Wikipedia API with language detection."""
    lang = "ru" if any(ord(c) > 127 for c in query) else "en"
    try:
        clean_query = query.replace('?', '').replace('!', '').strip()
        encoded = urllib.parse.quote(clean_query.replace(' ', '_'))
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        response = _http_session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "extract" in data:
                return f"According to Wikipedia [{lang}]: {data['extract']} (🔗 {data['content_urls']['desktop']['page']})"
    except Exception:
        pass
    return ""


def _ddg_search_task(query: str, timelimit: str = None):
    results = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            refined_query = query
            if len(query.split()) < 3:
                try:
                    suggestions = list(ddgs.suggestions(query))
                    if suggestions: refined_query = suggestions[0].get('phrase', query)
                except: pass
            
            ddg_results = list(
                ddgs.text(
                    refined_query,
                    max_results=DDG_RESULT_LIMIT,
                    timelimit=timelimit,
                )
            )
            if not ddg_results and timelimit:
                ddg_results = list(
                    ddgs.text(
                        refined_query,
                        max_results=DDG_RESULT_LIMIT,
                    )
                )
                
            for r in ddg_results:
                results.append({
                    'title': r.get('title'),
                    'body': r.get('body', ''),
                    'href': r.get('href'),
                    'source': 'DuckDuckGo'
                })
    except Exception as e:
        print(f"[search] DDGS task failed: {e}", file=sys.stderr)
    return results


def _google_search_task(query: str):
    results = []
    try:
        from googlesearch import search
        lang = "ru" if any(ord(c) > 127 for c in query) else "en"
        google_gen = search(
            query,
            num_results=GOOGLE_RESULT_LIMIT,
            lang=lang,
        )
        for url in google_gen:
            results.append({
                'title': url,
                'body': '',
                'href': url,
                'source': 'Google'
            })
    except Exception as e:
        print(f"[search] Google task failed: {e}", file=sys.stderr)
    return results


def internet_research(query: str):
    """Run internet research with MAXIMIZED parallel execution."""
    if not query or not query.strip():
        return "Sir, the search query appears to be empty."

    cached = _get_cached(query)
    if cached: return cached

    # 1. Start parallel engine search (DDG + Wiki + Google)
    query_lower = query.lower()
    needs_fresh = any(word in query_lower for word in ["latest", "version", "202", "new", "release", "update"])
    is_news = any(word in query_lower for word in ["news", "today", "yesterday", "current events"])
    timelimit = 'm' if is_news else ('y' if needs_fresh else None)

    results_data = []
    wiki_res = ""

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_ddg = executor.submit(_ddg_search_task, query, timelimit)
        f_wiki = executor.submit(_try_wikipedia, query)
        f_google = executor.submit(_google_search_task, query)
        
        # Wait for DDG first as it's primary
        results_data.extend(f_ddg.result())
        wiki_res = f_wiki.result()
        
        # Add Google results if DDG is thin
        if len(results_data) < 5:
            google_results = f_google.result()
            existing_urls = {r['href'] for r in results_data}
            for gr in google_results:
                if gr['href'] not in existing_urls:
                    results_data.append(gr)

    if not results_data and not wiki_res:
        return f"I'm sorry Sir, I was unable to retrieve any search results for '{query}'."

    # 2. Parallel Scraping of Top 2 Results
    output = [f"### Maximized Research: '{query}'\n"]
    display_results = results_data[:WEB_RESEARCH_DISPLAY_LIMIT]

    scrape_urls = []
    for r in display_results[:WEB_RESEARCH_SCRAPE_LIMIT]:
        if "wikipedia.org" not in r['href']:
            scrape_urls.append(r['href'])

    if scrape_urls:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(scrape_urls)) as executor:
            scraped_contents = list(executor.map(_fetch_page_content, scrape_urls))
            
            # Map back to results
            s_idx = 0
            for r in display_results[:2]:
                if r['href'] in scrape_urls:
                    if scraped_contents[s_idx]:
                        r['body'] = scraped_contents[s_idx]
                        r['enhanced'] = True
                    s_idx += 1

    # 3. Format Output
    for i, r in enumerate(display_results, start=1):
        source_label = f" ({r['source']}+Scraped)" if r.get('enhanced') else f" ({r['source']})"
        output.append(f"{i}. **{r['title']}**{source_label}")
        body = r['body'].strip()
        output.append(f"   {body[:1000]}..." if len(body) > 1000 else f"   {body}")
        output.append(f"   🔗 [Source]({r['href']})\n")

    if wiki_res:
        output.append(f"---\n{wiki_res}")

    final_result = "\n".join(output)
    _cache_result(query, final_result)
    return final_result


def get_news(city: str):
    if not city: return "Sir, please specify a city for the news."
    return internet_research(f"latest news in {city} today")


def get_weather(city: str):
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t+humidity:+%h+wind:+%w"
        response = _http_session.get(url, timeout=8)
        if response.status_code == 200 and response.text.strip():
            return f"The current weather in {city} is {response.text.strip()}."
    except Exception: pass
    return f"I was unable to retrieve the weather for {city} Sir."


def manage_web(action: str, query: str = "", city: str = ""):
    if action == "internet_research": return internet_research(query)
    elif action == "get_news": return get_news(city)
    elif action == "get_weather": return get_weather(city)
    return "Unknown web action."


def register_plugin():
    return [manage_web], {"manage_web": manage_web}
