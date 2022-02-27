import requests
import os
from twilio.rest import Client
from newsapi import NewsApiClient
from datetime import datetime

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

stock_api_key = os.environ.get("STOCK_API_KEY")
stock_api_url = "https://www.alphavantage.co/query"
stock_params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "TSLA",
    "outputsize": "compact",
    "datatype": "json",
    "apikey": stock_api_key
}
news_api_key = os.environ.get("NEWS_API_KEY")
news_api_url = f"https://newsapi.org/v2/everything?q={COMPANY_NAME}&apiKey={news_api_key}"
account_sid = os.environ.get("TWILIO_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOK")


def get_dict_key(minus: int) -> str:
    now_string_ym = datetime.now().strftime("%Y-%m-")
    now_int_d = int(datetime.now().strftime("%d"))
    if now_int_d <= 10:
        return f"{now_string_ym}-0{str(now_int_d-minus)}"
    else:
        return f"{now_string_ym}{str(now_int_d-minus)}"


# STEP 1: Use https://www.alphavantage.co
# When STOCK price increase/decreases by 5% between yesterday and the day before yesterday then print("Get News").
def get_change_in_price():
    stock_request = requests.get(stock_api_url, stock_params)
    raw_stock_data = stock_request.json()
    stock_data_yesterday = raw_stock_data["Time Series (Daily)"][get_dict_key(1)]
    stock_yesterday_price = float(stock_data_yesterday["4. close"])
    stock_data_db4y = raw_stock_data["Time Series (Daily)"][get_dict_key(2)]
    stock_db4y_price = float(stock_data_db4y["4. close"])
    # formula: ((num1-num2) / num2) * 100
    delta_price_percent = ((stock_yesterday_price - stock_db4y_price) / stock_db4y_price) * 100
    formatted_delta_price = float("{:.2f}".format(round(delta_price_percent, 2)))
    if formatted_delta_price >= 0.01:
        return f"🔺{formatted_delta_price}%"
    elif formatted_delta_price <= -0.01:
        return f"🔻{formatted_delta_price}%"


# STEP 2: Use https://newsapi.org
# Instead of printing ("Get News"), actually get the first 3 news pieces for the COMPANY_NAME.
def get_news_articles() -> dict:
    api = NewsApiClient(api_key=news_api_key)
    news_info = api.get_everything(q=COMPANY_NAME)
    articles_dict = {i: {
        "title": news_info["articles"][i]["title"],
        "description": news_info["articles"][i]["description"]
    } for i in range(3)}
    return articles_dict


price_change = get_change_in_price()
articles = get_news_articles()


# STEP 3: Use https://www.twilio.com
# Send a separate message with the percentage change and each article's title and description to your phone number.

client = Client(account_sid, auth_token)
message = client.messages.create(
    body=f"{STOCK}: {price_change}\n"
         f"Headline: {articles[0]['title']}\n"
         f"Brief: {articles[0]['description']}\n\n"
         f"Headline: {articles[1]['title']}\n"
         f"Brief: {articles[1]['description']}\n\n"
         f"Headline: {articles[2]['title']}\n"
         f"Brief: {articles[2]['description']}\n\n",
    from_=os.environ.get("PHONE2"),
    to=os.environ.get("PHONE1")
)


# Optional: Format the SMS message like this:


"""
TSLA: 🔺2%
Headline: Were Hedge Funds Right About Piling Into Tesla Inc. (TSLA)?. 
Brief: We at Insider Monkey have gone over 821 13F filings that hedge funds and prominent investors are required to 
file by the SEC The 13F filings show the funds' and investors' portfolio positions as of March 31st, near the height 
of the coronavirus market crash.
or
"TSLA: 🔻5%
Headline: Were Hedge Funds Right About Piling Into Tesla Inc. (TSLA)?. 
Brief: We at Insider Monkey have gone over 821 13F filings that hedge funds and prominent investors are required to 
file by the SEC The 13F filings show the funds' and investors' portfolio positions as of March 31st, near the height 
of the coronavirus market crash.
"""
