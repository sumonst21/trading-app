from os import close
import psycopg2
import psycopg2.extras
from config import configdb
from mlsc_utilities import fxcm_connect, db_connect
from mlsc_strategies import ScanForStrategy

# Connection to postgresql 
conn = db_connect()   
cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    
# get list of instruments from database
cursor.execute("""
    SELECT name FROM instruments 
""")
rows = cursor.fetchall()
symbols = [row['name'] for row in rows] # list comprehension

# FXCMapi connection
api = fxcm_connect()
assets = api.get_instruments_for_candles()

# main program
for asset in assets:
        if asset not in symbols:
            try:
                cursor.execute("INSERT INTO instruments (name, market_id, exchange) VALUES(%s, %s, %s)", (asset, 1, 'fxcm',))
                print(f"Added a new instrument {asset}")                
            except Exception as error:
                print ("Oops! An exception has occured:", error)
                print ("Exception TYPE:", type(error)) 

conn.close()
api.close()

# check for strategy triggers
ScanForStrategy()
