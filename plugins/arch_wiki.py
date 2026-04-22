import requests

def search_arch_wiki(query: str):
    """
    Search the official Arch Wiki for documentation and guides.
    Returns summaries and links for the top matches.
    """
    if not query: 
        return "Please provide a search term for the Arch Wiki."
    
    api_url = "https://wiki.archlinux.org/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 3
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = data.get("query", {}).get("search", [])
        
        if not results:
            return f"No Arch Wiki articles found for '{query}'."
            
        formatted_results = []
        for item in results:
            title = item['title']
            # Remove HTML tags from snippet
            snippet = item['snippet'].replace('<span class="searchmatch">', '').replace('</span>', '')
            page_url = f"https://wiki.archlinux.org/title/{title.replace(' ', '_')}"
            formatted_results.append(f"🔹 {title}\n{snippet}...\nRead more: {page_url}")
            
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Failed to reach Arch Wiki: {str(e)}"

def register_plugin():
    tools = [search_arch_wiki]
    mapping = {t.__name__: t for t in tools}
    return tools, mapping
