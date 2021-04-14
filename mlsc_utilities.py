from os import curdir
from socket import AI_PASSIVE
import psycopg2
import psycopg2.extras
from config import configdb
import pandas as pd
import fxcmpy
import ib_insync 
import time 
import sqlalchemy 

# Load variables
params = configdb()

# FXCMapi connection
def fxcm_connect():
    try:
        api = fxcmpy.fxcmpy(config_file='fxcm.cfg')
        print('api', api)
        return api
    except Exception as error:
        print ("Error connecting to fxcm API")  

# Interactive Brokers connection
def ib_connect():
    try:
        ib = ib_insync.IB()
        ib.connect('127.0.0.1', 7497, clientId=2)
        return ib
    except Exception as error:
        print ("Error connecting to IB API")      

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
        conn = psycopg2.connect(**params)
        return conn
    except psycopg2.OperationalError:
        print('Too many connections')
    except Exception as error:
        print ("Oops! An exception has occured: db_connect()", error)
        print ("Exception TYPE:", type(error))  

# Connection sqlalchemy ORM
def connect_alchemy():
    
    user = params['user']
    password = params['password']
    db = params['database']
    host = params['host']
    port = params['port']

    # We connect with the help of the PostgreSQL URL
    # postgresql://federer:grandestslam@localhost:5432/tennis
    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(user, password, host, port, db)
    print('url', url)
    # The return value of create_engine() is our connection object
    engine = sqlalchemy.create_engine(url, client_encoding='utf8')

    # We then bind the connection to MetaData()
    metadata = sqlalchemy.MetaData(bind=engine, reflect=True)

    return engine, metadata

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
    try:
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
    except:
        return False

def get_instruments_list(marketids = []):
    
    if len(marketids) == 0:
        cur.execute("""
            SELECT id FROM markets
        """)
        rows = cur.fetchall()
        marketids = [row['id'] for row in rows] 
        marketids = tuple(marketids)

    cur.execute("""
            SELECT t1.name, t1.id , t2.name, t1.market_id, t1.exchange_id FROM instruments t1, markets t2 WHERE t1.market_id = t2.id and t1.market_id in %s
        """, (marketids,))
    rows = cur.fetchall()

    symbols = [ tuple(row) for row in rows]
    return symbols
      
def postgresql_to_dataframe(conn, select_query, params, column_names):
    """
    Tranform a SELECT query into a pandas dataframe
    """
    cur = conn.cursor()
    try:
        cur.execute(select_query, params)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        cur.close()
        return 1
    
    # Naturally we get a list of tupples
    tupples = cur.fetchall()
    cur.close()
    
    # turn it into a pandas dataframe
    df = pd.DataFrame(tupples, columns=column_names)
    return df

def sql_count(table_name):
    sql = f'SELECT count(*) FROM {table_name};'
    cur.execute(sql)
    rows = cur.fetchone()[0]
    return rows

def get_market_list():
    cur.execute("""
        SELECT
            id,
            name
        FROM
            markets
    """)

    markets = cur.fetchall()
    return markets

def get_exchange_list():

    cur.execute("""
        SELECT
            id,
            exchange
        FROM
            exchanges
    """)
    exchanges = cur.fetchall()
    return exchanges