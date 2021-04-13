# fxmc-trading-app


Configuration:
---------

- Configuration steps:

      configure file fxcm.cfg with your FXCM credentials (you need to creare a FXCM account to get api credentials)
      configure file database.ini with your postgresql database, username, and password. 

- Installation steps:
      
      pip install -r requirements.txt
      py db_create.py
      py db_populate_instruments.py
      py db_populate_prices.py 
      
      
Exchanges Available:
---------
- FXCMAPI
- OANDAAPI (in development)
- ALPACAAPI (in development)

Technologies:
---------
- Python 3.8
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



