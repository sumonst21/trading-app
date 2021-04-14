from os import close
import psycopg2
import psycopg2.extras
from config import configdb
from mlsc_utilities import fxcm_connect, db_connect, get_instruments_list

# Connection to postgresql 
conn = db_connect()   
cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    
# get list of instruments from database
symbols = get_instruments_list()
symbols_name = [ symbol[0] for symbol in symbols]


# FXCMapi connection
api = fxcm_connect()
assets = api.get_instruments_for_candles()

# FXCM populate instruments
for asset in assets:
        if asset not in symbols_name:
            try:
                cursor.execute("INSERT INTO instruments (name, market_id, exchange_id) VALUES(%s, %s, %s)", (asset, 1, 1,))
                print(f"Added a new instrument {asset}")                
            except Exception as error:
                print ("Oops! An exception has occured:", error)
                print ("Exception TYPE:", type(error)) 

conn.commit()
conn.close()
api.close()


