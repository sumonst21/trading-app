# trading-import-app

Trading import app is designed to import market datas across a wide range of exchanges API available and to create market strategies in order to send automated notifications.

Exchanges:
---------
- FXCMAPI
- OANDAAPI (in development)
- ALPACAAPI (in development)

Technologies:
---------
- Python 3.8
- fxcmpy
- PostgreSQL
- FastAPI
- Semantic UI
- Jinja2


Features:
---------
- Import list of market instruments FOREX, INDEX, COMMODITIES and STOCKS.
- Get historical rates for any any day since 1999.
- Trading view Widget integration
- Breakout Strategy
- Email notifications

Filter:
-------
List of filter available for market analysis
- New intraday High
- New intraday Low

Installation
--------------
- Configuration Steps:
      
      Configure file fxcm.cfg with your credentials
      Configure file dabase.ini with database informations

- Installation steps:

      py db_create.py
      py db_populate_instruments.py
      py db_populate_prices.py 
      
