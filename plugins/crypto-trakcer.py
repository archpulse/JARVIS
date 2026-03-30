# 1. The function itself (there can be multiple)
def get_crypto_price(coin_name: str):
    """
    AI DESCRIPTION: Retrieves the current cryptocurrency price in USD.
    Call this function when the user asks for the price/exchange rate of a crypto (bitcoin, ethereum, dogecoin, etc.).
    Pass the coin name in English, lowercase.
    """
    # GOLDEN RULE #1: Write all imports INSIDE the function!
    # If imported at the top and the user lacks this library, the whole Axinix AI app will crash.
    import requests 
    
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_name.lower()}&vs_currencies=usd"
        response = requests.get(url, timeout=5).json()
        
        if coin_name.lower() in response:
            price = response[coin_name.lower()]["usd"]
            # GOLDEN RULE #2: Always return text! (The AI will read it out loud)
            return f"The current price of {coin_name} is {price} $"
        else:
            return f"I couldn't find a coin named {coin_name}."
    except Exception as e:
        return f"API Error: {e}"

# 2. Mandatory entry point for the loader (main.py)
def register_plugin():
    """
    GOLDEN RULE #3: This function must be named exactly like this.
    It returns a list of functions (for Google) and a dictionary (for internal code execution).
    """
    tools = [get_crypto_price]
    mapping = {
        "get_crypto_price": get_crypto_price
    }
    return tools, mapping
