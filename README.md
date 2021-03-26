# fxmc-trading-app


Exchanges Available:
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
- Position size calculation

Filter:
-------
List of filter available for market analysis
- New intraday High
- New intraday Low

Installation
--------------
- Configuration Steps:
      
      configure file fxcm.cfg with your FXCM credentials 
      configure file database.ini with database informations

- Installation steps:

      py db_create.py
      py db_populate_instruments.py
      py db_populate_prices.py 
      
