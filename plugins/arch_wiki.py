import requests
import concurrent.futures

def _fetch_wiki_intro(title: str):
    """Fetch the first few paragraphs of a wiki page."""
    api_url = "https://wiki.archlinux.org/api.php"
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": title,
        "format": "json"
    }
    try:
        resp = requests.get(api_url, params=params, timeout=5)
        data = resp.json()
        pages = data.get("query", {}).get("pages", {})
        for pid in pages:
            return pages[pid].get("extract", "")
    except: pass
    return ""

def search_arch_wiki(query: str):
    """
    Search Arch Wiki for documentation with parallel intro fetching.
    """
    if not query: return "Sir, please provide a search term for the Arch Wiki."
    
    api_url = "https://wiki.archlinux.org/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 3
    }
    
    try:
        response = requests.get(api_url, params=search_params, timeout=5)
        response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])
        
        if not results:
            return f"I couldn't find any Arch Wiki articles for '{query}', Sir."
            
        # Parallel fetch intros for all search results
        titles = [r['title'] for r in results]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(titles)) as executor:
            intros = list(executor.map(_fetch_wiki_intro, titles))

        formatted = [f"### Arch Wiki Intelligence: '{query}'\n"]
        for i, (item, intro) in enumerate(zip(results, intros), 1):
            title = item['title']
            url = f"https://wiki.archlinux.org/title/{title.replace(' ', '_')}"
            snippet = intro if intro else item['snippet'].replace('<span class="searchmatch">', '').replace('</span>', '')
            formatted.append(f"{i}. **{title}**")
            formatted.append(f"   {snippet[:800].strip()}...")
            formatted.append(f"   🔗 {url}\n")
            
        return "\n".join(formatted)
    except Exception as e:
        return f"Sir, I failed to reach the Arch Wiki: {str(e)}"

def register_plugin():
    tools = [search_arch_wiki]
    mapping = {"search_arch_wiki": search_arch_wiki}
    return tools, mapping
