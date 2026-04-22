import random
import re
import sys
import time
import json
import urllib.parse
import webbrowser
from collections import OrderedDict

import requests

_http_session = requests.Session()
_http_session.headers.update(
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
)

# Simple search result cache (avoids repeated queries)
_search_cache = OrderedDict()
_cache_max_size = 50
_cache_ttl_seconds = 300  # 5 minutes


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
        return "Search query is empty."

    # Check cache first
    cached = _get_cached(query)
    if cached:
        return f"[cached] {cached}"

    result = _do_search(query)
    _cache_result(query, result)
    return result


def _do_search(query: str) -> str:
    """Actual search implementation."""
    errors = []

    # 1. Try DDGS (DuckDuckGo Search) - Primary and most reliable
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            if results:
                lines = []
                for i, r in enumerate(results, start=1):
                    title = r.get('title')
                    link = r.get('href')
                    body = r.get('body', '').strip()
                    if title and body:
                        lines.append(f"{i}. {title}")
                        lines.append(f"   {body[:300]}...")
                        lines.append(f"   🔗 {link}")
                if lines:
                    return "\n".join(lines)
    except Exception as e:
        errors.append(f"DDGS: {e}")

    # 2. Try Google text search fallback
    try:
        from googlesearch import search
        import requests
        from bs4 import BeautifulSoup

        results = list(search(query, num_results=3, lang="ru"))
        if results:
            lines = []
            for i, url in enumerate(results[:3], start=1):
                try:
                    resp = requests.get(url, timeout=3)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        paragraphs = soup.find_all('p')
                        body = " ".join([p.get_text() for p in paragraphs[:3]])
                        if body:
                            body = body[:250].replace('\\n', ' ').strip()
                            title = soup.title.string if soup.title else "No title"
                            lines.append(f"{i}. {title}")
                            lines.append(f"   {body}...")
                            lines.append(f"   🔗 {url[:80]}")
                except Exception as req_err:
                    errors.append(f"Req: {req_err}")
            if lines:
                return "\\n".join(lines)
    except Exception as search_err:
        errors.append(f"GoogleSearch: {search_err}")
        print(f"[search] GoogleSearch failed: {search_err}", file=sys.stderr)

    # Try Wikipedia direct API with language fallback
    wiki_result = _try_wikipedia(query)
    if wiki_result:
        return wiki_result

    # Try Brave Search
    brave_result = _try_brave_search(query)
    if brave_result:
        return brave_result

    # Last resort: DuckDuckGo HTML
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        response = _http_session.get(search_url, timeout=10)
        if response.status_code == 200:
            text = response.text
            if not text:
                return f"Search unavailable for: {query}"
            # Try multiple snippet patterns
            snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)<', text)
            if snippets:
                return f"Result: {snippets[0][:400]}"
            alt_snippets = re.findall(r'data-tab="html"[^>]*>.*?<a[^>]*>([^<]+)<', text, re.DOTALL)
            if alt_snippets:
                return f"Result: {alt_snippets[0][:400]}"
    except Exception as e:
        errors.append(f"DDG HTML: {e}")

    if errors:
        return f"Search had issues: {'; '.join(errors[:2])}. Try: {query}"
    return f"Search is temporarily unavailable. Query: {query}"


def _try_wikipedia(query: str) -> str:
    """Try Wikipedia API with multiple languages."""
    # Try English first
    try:
        encoded = urllib.parse.quote(query.replace(' ', '_'))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        response = _http_session.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            if "extract" in data:
                title = data.get("title", query)
                extract = data["extract"]
                return f"📚 {title}\n{extract[:500]}"
    except Exception as e:
        print(f"[search] Wikipedia EN failed: {e}", file=sys.stderr)

    # Try Russian, Ukrainian
    for lang in ["ru", "uk"]:
        try:
            encoded = urllib.parse.quote(query.replace(' ', '_'))
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            response = _http_session.get(url, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if "extract" in data:
                    title = data.get("title", query)
                    extract = data["extract"]
                    return f"📚 [{lang}] {title}\n{extract[:500]}"
        except Exception:
            pass

    return ""


def _try_brave_search(query: str) -> str:
    """Try Brave Search API."""
    try:
        # Brave doesn't require API key for basic web search
        url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=3"
        response = _http_session.get(
            url,
            timeout=10,
            headers={
                "Accept": "application/json",
            }
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("web", {}).get("results", [])
            if results:
                lines = []
                for r in results[:3]:
                    title = r.get("title", "")
                    desc = r.get("description", "")
                    url_r = r.get("url", "")
                    if title and desc:
                        lines.append(f"• {title}")
                        lines.append(f"  {desc[:200]}")
                        if url_r:
                            lines.append(f"  🔗 {url_r[:80]}")
                if lines:
                    return "\n".join(lines)
    except Exception as e:
        print(f"[search] Brave failed: {e}", file=sys.stderr)
    return ""


def get_news(city: str):
    """Return a brief latest-news summary for a city."""
    if not city:
        return "City not specified."
    return internet_research(f"latest news in {city} today")


def get_weather(city: str):
    """Return current weather from wttr.in with detailed fallback handling."""
    if not city:
        return "City not specified."

    city_clean = city.strip().replace(" ", "+")

    # Try wttr.in with multiple format attempts
    for format_code in ["3", "j1"]:
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city_clean)}?format={format_code}"
            response = _http_session.get(url, timeout=10)
            if response.status_code == 200:
                text = response.text.strip()
                if text and len(text) > 5:
                    if format_code == "3":
                        return f"🌤 {text}"
                    if format_code == "j1":
                        try:
                            data = response.json()
                            current = data.get("current_condition", [{}])[0]
                            temp = current.get("temp_C", "?")
                            feels = current.get("FeelsLikeC", "?")
                            desc = current.get("weatherDesc", [{}])[0].get("value", "unknown")
                            humidity = current.get("humidity", "?")
                            wind = current.get("windspeedKmph", "?")
                            return f"🌤 Weather in {city}: {temp}°C, feels like {feels}°C, {desc}, humidity {humidity}%, wind {wind} km/h"
                        except Exception:
                            return f"🌤 {text}"
        except requests.exceptions.RequestException:
            continue

    # Fallback: Wikipedia + wttr.in with coordinates
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(city_clean)}"
        response = _http_session.get(wiki_url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            coordinates = data.get("coordinates", {})
            if coordinates:
                lat = coordinates.get("lat", "")
                lon = coordinates.get("lon", "")
                if lat and lon:
                    direct_url = f"https://wttr.in/{lat},{lon}?format=3"
                    response2 = _http_session.get(direct_url, timeout=10)
                    if response2.status_code == 200:
                        return f"🌤 {response2.text.strip()}"
    except Exception:
        pass

    return f"🌤 Weather unavailable for {city}. Check your connection."


def play_music(query: str):
    """Open YouTube search for a track."""
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+official"
    webbrowser.open(url)
    return f"Opening YouTube: {query}"


def play_on_spotify(query: str):
    """Open Spotify Web search for a track."""
    url = f"https://open.spotify.com/search/{query.replace(' ', '%20')}"
    webbrowser.open(url)
    return f"Opening Spotify: {query}"


def roll_dice():
    """Roll one six-sided die."""
    return f"🎲 Dice roll result: {random.randint(1, 6)}"


def coin_flip():
    """Flip a coin."""
    result = "Heads" if random.random() > 0.5 else "Tails"
    return f"🪙 Coin flip: {result}"


def manage_web(action: str, query: str = "", city: str = ""):
    """Manage web functions. Actions: 'internet_research' (needs query), 'get_news' (needs city), 'get_weather' (needs city), 'play_music' (needs query), 'play_on_spotify' (needs query), 'roll_dice', 'coin_flip'."""
    if action == "internet_research": return internet_research(query)
    elif action == "get_news": return get_news(city)
    elif action == "get_weather": return get_weather(city)
    elif action == "play_music": return play_music(query)
    elif action == "play_on_spotify": return play_on_spotify(query)
    elif action == "roll_dice": return roll_dice()
    elif action == "coin_flip": return coin_flip()
    else: return "Unknown action."

def register_plugin():
    tools = [manage_web]
    mapping = {t.__name__: t for t in tools}
    return tools, mapping
