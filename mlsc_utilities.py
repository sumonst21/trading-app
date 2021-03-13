import psycopg2
import psycopg2.extras
from config import configdb
import fxcmpy
import time

# FXCMapi connection
def fxcm_connect():
    api = fxcm_handler()
    while not api:
        print('fxcm reconnecting in 45 seconds')
        time.sleep(45)
        api = fxcm_handler()
    print('api central', api)
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
    print('conn central', conn)
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