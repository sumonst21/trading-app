import psycopg2
import psycopg2.extras
from config import configdb
import fxcmpy
from mlsc_utilities import db_connect, fxcm_connect

api = fxcm_connect()
print(api)

api.open_trade('EUR/GBP', is_buy=True, amount=10, time_in_force='IOC', order_type='AtMarket', is_in_pips=False, stop=0.85754) 
api.close()