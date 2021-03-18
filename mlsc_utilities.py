from socket import AI_PASSIVE
import psycopg2
import psycopg2.extras
from config import configdb
import fxcmpy
import time
import sys

# FXCMapi connection
def fxcm_connect():
    try:
        api = fxcmpy.fxcmpy(config_file='fxcm.cfg')
        print('api', api)
        return api
    except Exception as error:
        print ("Error connecting to fxcm API")  
        sys.exit()

# Connection to postgresql
def db_connect():
    conn = db_handler()
    while not conn:
        print('reconnecting database in 45....')
        time.sleep(45)
        conn = db_handler()
    return conn

def db_handler():
    try:
        params = configdb()
        conn = psycopg2.connect(**params)
        return conn
    except psycopg2.OperationalError:
        print('Too many connections')
    except Exception as error:
        print ("Oops! An exception has occured: db_connect()", error)
        print ("Exception TYPE:", type(error))  

# general use functions
conn = db_connect()   
cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

def GetSymbolName(symbol_id):
    cur.execute("""
        SELECT  
            name                 	    
        FROM 
            instruments
        WHERE 
            id = %s
    """, (symbol_id,))       
    symbol_name = cur.fetchone()['name']

    return symbol_name

def GetSymbolId(symbol_name):
    cur.execute("""
        SELECT  
            id                 	    
        FROM 
            instruments
        WHERE 
            name = %s
    """, (symbol_name,))       
    symbol_id = cur.fetchone()['id']
    
    return symbol_id    

