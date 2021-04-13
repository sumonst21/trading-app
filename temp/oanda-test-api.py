import requests
import json
import numpy as np
import pandas as pd


API = "api-fxpractice.oanda.com"
STREAM_API = "stream-fxtrade.oanda.com"

ACCESS_TOKEN = "f-ffffffffffffff"
ACCOUNT_ID = "101-fff-ffffff-fff"


PRICING_PATH = f'/v3/accounts/{ACCOUNT_ID}/pricing' 

query = {"instruments": "USD_CAD"} 
headers = {"Authorization": "Bearer "+ ACCESS_TOKEN}    

response = requests.get("https://"+API+PRICING_PATH, headers=headers, params=query)
price_history = response.json()
print(price_history)