from socket import AI_PASSIVE
import psycopg2
import psycopg2.extras
from config import configdb
import fxcmpy
import time



# FXCMapi connection
def fxcm_connect():
    api = fxcm_handler()
    while not api:
        print('api:', api)
        del api
        print('fxcm reconnecting in 45 seconds')
        time.sleep(45)
        api = fxcm_handler()
    return api

def fxcm_handler():
    try:
        api = fxcmpy.fxcmpy(config_file='fxcm.cfg')
        return api
    except Exception as error:
        print ("Oops! An exception has occured: fxcm_connect()", error)
        print ("Exception TYPE:", type(error))  


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

