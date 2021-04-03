import requests
import json
import numpy as np
import pandas as pd


API = "api-fxpractice.oanda.com"
STREAM_API = "stream-fxtrade.oanda.com"

ACCESS_TOKEN = "4240ecde590294a01347cdde1f8c959c-d1e03901e1e4c6ea2a1b32fb37cba2ef"
ACCOUNT_ID = "101-011-18048207-001"


PRICING_PATH = f'/v3/accounts/{ACCOUNT_ID}/pricing' 

query = {"instruments": "USD_CAD"} 
headers = {"Authorization": "Bearer "+ ACCESS_TOKEN}    

response = requests.get("https://"+API+PRICING_PATH, headers=headers, params=query)
price_history = response.json()
print(price_history)