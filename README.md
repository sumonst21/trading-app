# fxmc-trading-app


Configuration Files:
---------

- fxcm.cfg

      [FXCM]
      log_level = error
      log_file = 'log.txt'
      access_token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

- database.ini
      
      [postgresql]
      database = tradingapp
      user = postgres
      password = xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      host = 127.0.0.1
      port = 5432

- Install dependences
      
      sudo apt-get update
      sudo apt install python3-pip
      sudo apt-get install gunicorn
      sudo apt update
      
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
- backtrader
- boto3

Features:
---------
- Import list of market instruments FOREX, INDEX, COMMODITIES and STOCKS.
- Get historical rates for any any day since 1999.
- Trading view Widget integration
- Breakout Strategy
- Email notifications
- Position size calculation



