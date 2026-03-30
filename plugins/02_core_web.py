import random
import re
import webbrowser

import requests
from duckduckgo_search import DDGS

_http_session = requests.Session()
_http_session.headers.update(
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
)


def internet_research(query: str):
    """Run internet research with multiple lightweight fallbacks."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if results:
            return "\n".join(
                f"{i}. {item['title']}: {item['body']}"
                for i, item in enumerate(results, start=1)
            )
    except Exception:
        pass

    try:
        wiki_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            f"{query.replace(' ', '_')}"
        )
        response = _http_session.get(wiki_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "extract" in data:
                return f"{data.get('title', query)}: {data['extract']}"
    except requests.RequestException:
        pass

    try:
        search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        response = _http_session.get(search_url, timeout=8)
        if response.status_code == 200:
            snippets = re.findall(
                r'class="result__snippet"[^>]*>([^<]+)<', response.text
            )
            if snippets:
                return f"Result: {snippets[0]}"
    except requests.RequestException:
        pass

    return f"Search is temporarily unavailable. Query: {query}"


def get_news(city: str):
    """Return a brief latest-news summary for a city."""
    return internet_research(f"latest news in {city}")


def get_weather(city: str):
    """Return current weather from wttr.in."""
    try:
        response = _http_session.get(f"https://wttr.in/{city}?format=3", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        return f"Weather service error (HTTP {response.status_code})"
    except requests.exceptions.Timeout:
        return "Weather request timeout."
    except requests.exceptions.ConnectionError:
        return "No internet connection."
    except requests.RequestException as exc:
        return f"Weather request error: {exc}"


def play_music(query: str):
    """Open YouTube search for a track."""
    webbrowser.open(
        f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}+official"
    )
    return f"Opening: {query}"


def play_on_spotify(query: str):
    """Open Spotify Web search for a track."""
    webbrowser.open(f"https://open.spotify.com/search/{query.replace(' ', '%20')}")
    return f"Opening Spotify: {query}"


def roll_dice():
    """Roll one six-sided die."""
    return f"Dice roll result: {random.randint(1, 6)}"


def coin_flip():
    """Flip a coin."""
    return "Result: Heads" if random.random() > 0.5 else "Result: Tails"


def register_plugin():
    tools = [
        internet_research,
        get_news,
        get_weather,
        play_music,
        play_on_spotify,
        roll_dice,
        coin_flip,
    ]
    mapping = {
        "internet_research": internet_research,
        "get_news": get_news,
        "get_weather": get_weather,
        "play_music": play_music,
        "play_on_spotify": play_on_spotify,
        "roll_dice": roll_dice,
        "coin_flip": coin_flip,
    }
    return tools, mapping
