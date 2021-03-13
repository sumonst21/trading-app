from config import configemail
import psycopg2
import psycopg2.extras
import smtplib, ssl
from mlsc_utilities import db_connect, fxcm_connect

# Main scanner for ALL strategies
def ScanForStrategies():

    # Connection to postgresql
    print('db-ScanForStrategies')
    conn = db_connect()   
    cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    # get list of strategies_instruments
    cur.execute("""
        SELECT 
	        t2.symbol_id id,
	        t1.name strategy_name
        FROM 
	        strategies t1,
	        strategies_symbol t2,
	        instruments t3
        WHERE
	        t1.id = t2.strategy_id and
	        t2.symbol_id = t3.id and
            t2.status = 'new'
    """)
    symbols = cur.fetchall()

    for symbol in symbols:
   
        symbol_id, strategy_name = symbol

        

        #if strategy_name == 'breakout_1h_ema_50': #fix it when add a new strategy
        check_for_alert_bo1h(symbol_id)



# General Functions
def GetDailyBias(symbolid):     
    
    print('db-GetDailyBias(symbolid)')
    conn = db_connect()   
    cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    
    cur.execute("""
        SELECT 
	        strategy_bias
        FROM 
	        strategies_symbol
        WHERE
			symbol_id = %s
    """, (symbolid,))
    strategy_bias = cur.fetchone()['strategy_bias']  

    conn.close()
    return strategy_bias

def SendEmailTo(message):
    paramsEmail = configemail()

    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(paramsEmail['email_host'], paramsEmail['email_port'], context=context) as server:
        server.login(paramsEmail['email_address'], paramsEmail['email_password'])  

        email_message = f"Subject: Trade Notification MCFX\n\n"
        email_message += "\n\n".join(message)

        server.sendmail(paramsEmail['email_address'], paramsEmail['email_address'], email_message)
   
# Trading Functions
def OpenBuyPosition(params):

    # FXCMapi connection
    print('api-Openbuyposition')
    api = fxcm_connect()

    symbol_name, stop_loss = params

    # check any open trade for symbol_name
    amount = 10
    api.open_trade(symbol_name, is_buy=True, amount=amount, time_in_force='IOC', order_type='AtMarket', is_in_pips=False, stop=stop_loss)
             
    api.close()

def OpenSellPosition(params):
    symbol_name, stop_loss = params

    # FXCMapi connection
    print('api-Opensellposition')
    api = fxcm_connect()


    # check any open trade for symbol_name
    amount = 10
    api.open_trade(symbol_name, is_buy=False, amount=amount, time_in_force='IOC', order_type='AtMarket', is_in_pips=False, stop=stop_loss)         
    api.close()    

# Strategies
def check_for_alert_bo1h(symbol_id):
    
    print('db-check_for_alert_bo1h(symbol_id)')
    conn = db_connect()   
    cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    message = []
    
    daily_bias = GetDailyBias(symbol_id)
  
    # get instrument name
    cur.execute("""
        SELECT  
            name                 	
        FROM 
            instruments
        WHERE 
            id = %s
    """, (symbol_id,))       
    symbol_name = cur.fetchone()['name']
    
    # get max/min previous D1 candle
    cur.execute("""
        SELECT  
            bidhigh, 
            bidlow
        FROM 
            prices_fxcm_api 
        WHERE 
            timeframe = 'D1' and 
            symbolid= %s
    """, (symbol_id,))

    rowsd1 = cur.fetchall()[-1] # fetch last candle instead

    high_previous_day = rowsd1['bidhigh']
    low_previous_day = rowsd1['bidlow']

    # get max/min last closed H1 candle  
    cur.execute("""
        SELECT  
            bidclose,
            bidlow,
            bidhigh
        FROM 
            prices_fxcm_api 
        WHERE 
            timeframe = 'H1' and 
            symbolid= %s
    """, (symbol_id,))

    rowsh1 = cur.fetchall()[-1] # fetch last candle

    close_previous_h1 = rowsh1['bidclose']
    low_previous_h1 = rowsh1['bidlow']
    high_previous_h1 = rowsh1['bidhigh']

    # main logic       
    if daily_bias == 'Long':
        if close_previous_h1 > high_previous_day:
            message.append(f'{symbol_name} - Long with trend | Previous day high: {high_previous_day} | Previous Close H1: {close_previous_h1} | Previous Low H1: {low_previous_h1}')   
            OpenBuyPosition((symbol_name, low_previous_h1))
    elif daily_bias == 'Short':
        if close_previous_h1 < low_previous_day:
            message.append(f'{symbol_name} - Short with trend | Previous day Low: {low_previous_day} | Previous Close H1: {close_previous_h1} | Previous High H1: {high_previous_h1}')
            OpenSellPosition((symbol_name, high_previous_h1))

    if message:
        SendEmailTo(message)
    



    conn.close()