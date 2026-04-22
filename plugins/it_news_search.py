def search_it_news(query: str = "IT world news"):
    """
    AI DESCRIPTION: Searches for the latest IT and technology news using DuckDuckGo.
    Use this when the user asks for news about programming, tech companies, or general IT updates.
    """
    from ddgs import DDGS
    
    try:
        with DDGS() as ddgs:
            # Use the newer 'text' method which returns a generator of results
            results = [r for r in ddgs.text(query, max_results=5)]
            if not results:
                return f"No IT news found for '{query}'."
            
            output = [f"Latest IT news for '{query}':"]
            for r in results:
                title = r.get('title')
                link = r.get('href')
                snippet = r.get('body', 'No description available.')
                output.append(f"- {title}\n  {snippet}\n  🔗 {link}")
            
            return "\n".join(output)
    except Exception as e:
        return f"Error searching IT news: {e}"

def register_plugin():
    tools = [search_it_news]
    mapping = {"search_it_news": search_it_news}
    return tools, mapping
