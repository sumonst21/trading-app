from config import configemail
import psycopg2
import psycopg2.extras
import smtplib, ssl
from mlsc_utilities import db_connect, fxcm_connect, GetSymbolName, GetSymbolId
from math import fsum

# Connection to postgresql
conn = db_connect()   
cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

# Main scanner for ALL strategies
def ScanForStrategies():

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
    
    cur.execute("""
        SELECT 
	        strategy_bias
        FROM 
	        strategies_symbol
        WHERE
			symbol_id = %s
    """, (symbolid,))
    strategy_bias = cur.fetchone()['strategy_bias']  

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

# Risk Management
def size_position(price, stop, risk, method=0, exchange_rate=None, JPY_pair=False):
    # size_position(0.77520, 0.77400, risk=2, method=1, JPY_pair = False)

    #    '''
    #    Helper function to calcuate the position size given a known amount of risk.
    # 
    #    *Args*
    #    - price: Float, the current price of the instrument
    #    - stop: Float, price level of the stop loss
    #    - risk: Float, the amount of the account equity to risk
    
    #    *Kwargs*
    #    - JPY_pair: Bool, whether the instrument being traded is part of a JPY
    #    pair. The muliplier used for calculations will be changed as a result.
    #    - Method: Int,
    #        - 0: Acc currency and counter currency are the same
    #        - 1: Acc currency is same as base currency
    #        - 2: Acc currency is neither same as base or counter currency
    #    - exchange_rate: Float, is the exchange rate between the account currency
    #    and the counter currency. Required for method 2.
    #    '''

    if JPY_pair == True: #check if a YEN cross and change the multiplier
        multiplier = 0.01
        divisor = 100
    else:
        multiplier = 0.0001
        divisor = 10000
    #Calc how much to risk
    acc_value = 1000 #self.broker.getvalue()
    cash_risk = acc_value * (risk/100)
    stop_pips_int = abs((price - stop) / multiplier)
    pip_value = cash_risk / stop_pips_int
    pip_value_std = (multiplier/price) * divisor

    
    print('price', price)
    print('stop', stop )
    print('method', method)
    print('exchange_rate', exchange_rate)
    print('stop_pips_int', stop_pips_int)
    print('pip_value', pip_value)
    print('pip_value_std', pip_value_std)

    if method == 1:
        #pip_value = pip_value * price
        units = (pip_value * divisor) / pip_value_std
        units_fxcm = units / 1000
        return units_fxcm
 
    elif method == 2:
        #pip_value = pip_value * exchange_rate
        units = (pip_value * divisor) / pip_value_std
        units_fxcm = units / 1000
        return units_fxcm
 
    else: # is method 0
        units = (pip_value * divisor) / pip_value_std
        units_fxcm = units / 1000
        return units_fxcm

# Trading Functions
def OpenBuyPosition(params):

    # api connection
    try:
        api = fxcm_connect()
        symbol_name, stop_loss, close_previous_h1 = params
        close_previous_h1 = float(close_previous_h1)
        risk = 2
        JPY_pair = False

        # set stop_loss, and take_profit 
        if 'JPY' in symbol_name:
            stop = fsum([stop_loss, -0.010])
            pips = (close_previous_h1 - stop) 
            take_profit = (round(pips,3) * 2) + close_previous_h1
            JPY_pair = True
        else:
            stop = fsum([stop_loss, -0.00010])
            pips = (close_previous_h1 - stop) 
            take_profit = (round(pips,5) * 2) + close_previous_h1
    
        # set method for position size
        if 'EUR/AUD' in symbol_name:
            method = 0
        elif 'AUD' in symbol_name: 
            method = 1
        else:
            method = 2
            symbol_exchage = 'AUD' + symbol_name[3:]
        
            cur.execute("""
                SELECT 
                    bidclose
                FROM
                    prices_fxcm_api t1,
                    instruments t2
                WHERE
                    t1.symbolid=t2.id and
                    t2.name = %s and
                    date = (
                            SELECT 
                                max(date) max_date
                            FROM
                                prices_fxcm_api t1,
                                instruments t2
                            WHERE
                                t1.symbolid=t2.id and
                                t2.name = %s and
                            t1.timeframe = 'H1'
                        )
            """, (symbol_exchage, symbol_exchage, ))

            exchange_rate = cur.fetchone()
            print('exchange_rate', exchange_rate)
            rate = exchange_rate['bidclose']
            rate = float(rate)
    
        # set position size
        size = size_position(price=close_previous_h1, stop=stop, risk=risk, method=method, exchange_rate=rate, JPY_pair=JPY_pair)
        print('size', size, symbol_name)

        #open order
        api.open_trade(symbol_name, is_buy=True, amount=size, time_in_force='IOC', limit = take_profit, order_type='AtMarket', is_in_pips=False, stop=stop)
        api.close()
    except:
        print('OpenBuyOrder Error',)

def OpenSellPosition(params):

    # api connection
    try:
        api = fxcm_connect()
        symbol_name, stop_loss, close_previous_h1 = params
        close_previous_h1 = float(close_previous_h1)
        risk = 2
        rate = 0
        JPY_pair = False    
 
        # add extra pips stop_loss
        if 'JPY' in symbol_name:
            stop = fsum([stop_loss, 0.010])
            pips = (stop - close_previous_h1) 
            take_profit = close_previous_h1 - (round(pips,3) * 2)
            JPY_pair = True
        else:
            stop = fsum([stop_loss, 0.00010])
            pips = (stop - close_previous_h1) 
            take_profit = close_previous_h1 - (round(pips,5) * 2)   
        print('symbol_name', symbol_name)
        # set method for position size
        if 'USD' in symbol_name[-3:]:
            method = 0
        elif 'USD' in symbol_name[:3]:
            method = 1
        else:
            method = 2
            symbol_exchage = 'USD' + symbol_name[3:]
            isValid = GetSymbolId(symbol_exchage)

            if not isValid:
                symbol_exchage = symbol_name[-3:] + '/USD'
            

            print('symbol_exchage', symbol_exchage)
            cur.execute("""
                SELECT 
                    bidclose
                FROM
                    prices_fxcm_api t1,
                    instruments t2
                WHERE
                    t1.symbolid=t2.id and
                    t2.name = %s and
                    date = (
                            SELECT 
                                max(date) max_date
                            FROM
                                prices_fxcm_api t1,
                                instruments t2
                            WHERE
                                t1.symbolid=t2.id and
                                t2.name = %s and
                            t1.timeframe = 'H1'
                        )
            """, (symbol_exchage, symbol_exchage, ))

            exchange_rate = cur.fetchone()
            print('exchange_rate', exchange_rate)
            rate = exchange_rate['bidclose']
            rate = float(rate)
 
        # set position size
        size = size_position(price=close_previous_h1, stop=stop, risk=risk, method=method, exchange_rate=rate, JPY_pair=JPY_pair)
        print('size', size, symbol_name)

        #open order
        api.open_trade(symbol_name, is_buy=False, amount=size, time_in_force='IOC', limit = take_profit, order_type='AtMarket', is_in_pips=False, stop=stop)         
        api.close()    
    except Exception as error:
        print('OpenSellOrder error', params, 'error:', error, symbol_name, size, take_profit, stop)

def UpdateNewTrade():
    
    # api connection
    api = fxcm_connect()
    trades = api.get_open_positions(kind = 'list')

    # get list of strategies_instruments
    cur.execute("""
        SELECT 
            t2.id
        FROM 
	        strategies_symbol t1,
	        instruments t2
        WHERE

	        t1.symbol_id = t2.id and
            t1.status = 'new'
    """)
    rows = cur.fetchall()
    symbols = [row['id'] for row in rows] # list comprehension

    for trade in trades:

        symbol_id = GetSymbolId(trade.get('currency'))

        if symbol_id in symbols:

     
            tradeId = trade.get('tradeId')
            entry = trade.get('open') 
            stop = trade.get('stop')
            take_profit = trade.get('limit')
            status = 'trading'
            # Update single record now
            sql_update_query = """
            UPDATE 
	            strategies_symbol
            SET
	            entry_point = %s, 
	            stop_loss = %s, 
	            take_profit = %s, 
	            status = %s,
                trade_id = %s
            WHERE
	            symbol_id = %s
            """
            cur.execute(sql_update_query, (entry, stop, take_profit, status, tradeId, symbol_id ))
            conn.commit()

            print('Trade updated successfully')
    api.close()

# Strategies
def check_for_alert_bo1h(symbol_id):
    
    message = []
    
    daily_bias = GetDailyBias(symbol_id)
  
    # get instrument name
    symbol_name = GetSymbolName(symbol_id) 
    
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
            print(f'{symbol_name} - Long with trend | Previous day high: {high_previous_day} | Previous Close H1: {close_previous_h1} | Previous Low H1: {low_previous_h1}')   
            print('symbol_name', symbol_name)
            response = OpenBuyPosition((symbol_name, low_previous_h1, close_previous_h1))
            UpdateNewTrade() # incluir condicional
    elif daily_bias == 'Short':
        if close_previous_h1 < low_previous_day:
            message.append(f'{symbol_name} - Short with trend | Previous day Low: {low_previous_day} | Previous Close H1: {close_previous_h1} | Previous High H1: {high_previous_h1}')
            print(f'{symbol_name} - Short with trend | Previous day Low: {low_previous_day} | Previous Close H1: {close_previous_h1} | Previous High H1: {high_previous_h1}')
            print('symbol_name', symbol_name)
            response = OpenSellPosition((symbol_name, high_previous_h1, close_previous_h1))
            UpdateNewTrade() # incluir condicional
    if message:
        SendEmailTo(message)
    


