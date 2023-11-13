import datetime
import requests
from gnews import GNews
import pyshorteners
import telegram.ext
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

Token='6361600875:AAEtIhUTu3RoxsDtVlddAr7npew-7zjsNV4'

updater = telegram.ext.Updater('6361600875:AAEtIhUTu3RoxsDtVlddAr7npew-7zjsNV4',use_context=True)

dispatcher = updater.dispatcher


def start(update, context):
    update.message.reply_text('Hi! here are some news with price')
    
    
def help(update, context):
    update.message.reply_text(
        """/start - start the bot
        /help - help for more
        /price - get the price of the coin with news
        """)
        
#write a function for my script
def price(update, context):
    context.user_data['waiting_for_symbol'] = True
    update.message.reply_text('Enter the cryptocurrency symbol (e.g., BTC, ETH): ')
    
    
def handle_symbol(update, context):
    symbol = update.message.text.upper()
    crypto_details = get_crypto_details(symbol)
    if crypto_details:
        update.message.reply_text(f"Crypto details for {symbol}:\n{crypto_details}")
        news_portal(symbol, update)
    else:
        update.message.reply_text("There was an error retrieving the cryptocurrency details.")

    context.user_data['waiting_for_symbol'] = False

BING_SEARCH_API_KEY = 'ac298abf540d41f4a1b5069cab81b079'

def get_news_bing(keyword):
    headers = {
        'Ocp-Apim-Subscription-Key': BING_SEARCH_API_KEY,
    }
    params = {
        'q': keyword + ' Token News',
        'count': 5,
        'offset': 0,
        'mkt': 'en-US',
        'safesearch': 'Moderate',
    }
    response = requests.get('https://api.bing.microsoft.com/v7.0/news/search', headers=headers, params=params)
    response.raise_for_status()
    search_results = response.json()
    return search_results['value']

def get_crypto_details(symbol):
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '3b60b88d-7c35-4828-826b-392f40c02902',
    }
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {
        'symbol': symbol,
        'convert': 'USD'
    }
    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()

    if response.status_code == 200:
        try:
            coin_data = data['data'][symbol]
            usd_price = coin_data['quote']['USD']['price']
            high_24h = coin_data['quote']['USD'].get('high_24h', 'N/A')
            low_24h = coin_data['quote']['USD'].get('low_24h', 'N/A')
            change_1h = coin_data['quote']['USD'].get('percent_change_1h', 'N/A')
            change_24h = coin_data['quote']['USD'].get('percent_change_24h', 'N/A')
            change_7d = coin_data['quote']['USD'].get('percent_change_7d', 'N/A')
            market_cap = coin_data['quote']['USD'].get('market_cap', 'N/A')
            volume_24h = coin_data['quote']['USD'].get('volume_24h', 'N/A')
            market_cap_rank = coin_data.get('cmc_rank', 'N/A')
            fully_diluted_market_cap = coin_data['quote']['USD'].get('fully_diluted_market_cap', 'N/A')

            # -------->Formatting the display output
            display_output = f"${usd_price:.2f} | {'N/A' if high_24h == 'N/A' else f'{high_24h:.2f}'} | {'N/A' if low_24h == 'N/A' else f'{low_24h:.2f}'}\n"
            display_output += f"1h: {'N/A' if change_1h == 'N/A' else f'{change_1h:.2f}%'}\n"
            display_output += f"24h: {'N/A' if change_24h == 'N/A' else f'{change_24h:.2f}%'}\n"
            display_output += f"7d: {'N/A' if change_7d == 'N/A' else f'{change_7d:.2f}%'}\n"
            display_output += f"Cap: {'N/A' if market_cap_rank == 'N/A' else f'{market_cap_rank}th'} | {'N/A' if market_cap == 'N/A' else f'${market_cap/1e6:.1f}M'}\n"
            display_output += f"FDV: {'N/A' if fully_diluted_market_cap == 'N/A' else f'${fully_diluted_market_cap/1e9:.1f}B'}\n"
            display_output += f"Vol: {'N/A' if volume_24h == 'N/A' else f'${volume_24h/1e6:.1f}M'}\n"

            return display_output
        except KeyError as e:
            print(f"KeyError: The key {e} was not found in the response. Here is the data received:\n{data}")
            return None
    else:
        print(f"Error: The API call was not successful. Status code: {response.status_code}")
        print(f"Response: {data}")
        return None

def news_portal(symbol, update):
    gnews_results = GNews().get_news(symbol + ' Token News')
    bing_results = get_news_bing(symbol + ' Token News')

    combined_news = []

    for news_item in gnews_results[:5]:
        title = news_item['title']
        link = news_item['url']
        title_parts = title.split(" - ")
        if len(title_parts) > 1:
            publisher = title_parts[-1]
            title = " - ".join(title_parts[:-1])
        else:
            publisher = "Unknown Publisher"
        date = news_item.get('published date', datetime.datetime.now()).split('T')[0]
        combined_news.append((date, publisher, title, link))

    for result in bing_results[:5]:
        title = result['name']
        url = result['url']
        description = result.get('description', 'No description available')
        publisher = result['provider'][0]['name'] if result['provider'] else "Unknown Publisher"
        date = result.get('datePublished', datetime.datetime.now().isoformat()).split('T')[0]
        combined_news.append((date, publisher, title, url))

    type_tiny = pyshorteners.Shortener()  # Initialize the Shortener object

    combined_news.sort(key=lambda x: (x[0], x[1]))

    news_by_publisher = {}
    for date, publisher, title, url in combined_news:
        if publisher not in news_by_publisher:
            news_by_publisher[publisher] = []
        short_url = type_tiny.tinyurl.short(url)  # Shorten the URL
        news_by_publisher[publisher].append((date, title, short_url))  # Add the shortened URL to the list

    for publisher, articles in news_by_publisher.items():
        update.message.reply_text(f"\nNews by: {publisher}")
        for date, title, short_url in articles:
            update.message.reply_text(f"Date: {date}\nTitle: {title}\nURL: {short_url}")

# if __name__ == "__main__":
#     symbol = input("Enter the cryptocurrency symbol (e.g., BTC, ETH): ").upper()
#     crypto_details = get_crypto_details(symbol)
#     if crypto_details:
#         print(f"Crypto details for {symbol}:\n{crypto_details}")
#     else:
#         print("There was an error retrieving the cryptocurrency details.")
#     news_portal(symbol)

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('price', price))

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_symbol))

updater.start_polling()
updater.idle()