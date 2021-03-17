import psycopg2
import psycopg2.extras
import datetime as dt
import time 
import pytz
from mlsc_utilities import db_connect, fxcm_connect
from mlsc_strategies import ScanForStrategies

def Isprocessed(params):
    try:
        sql = "select * from prices_fxcm_api WHERE symbolid = %s and timeframe = %s and date = %s"
        cur.execute(sql, (params['symbol'], params['timeframe'], params['date'],))
        
        return cur.rowcount
    
    except (Exception, psycopg2.Error) as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))   

def DataframeToSql(dataframe):
    try:
        # creating column list for insertion
        cols = historical_data.columns.tolist()
        cols.insert(0, 'date')
        cols = ",".join([str(i) for i in cols])

        # Insert DataFrame records one by one.
        for i,row in dataframe.iterrows():

            dictproc = {    
                "date": i, 
                "symbol": row.symbolid, 
                "timeframe": row.timeframe
            }
            
            if Isprocessed(dictproc) == 0:
                sql = "INSERT INTO prices_fxcm_api (" +cols + ") VALUES (" + "%s,"*(len(row)) + "%s)"
                cur.execute("SET TIME ZONE 'Australia/Sydney';") 
                cur.execute(sql, (i, row.bidopen, row.bidclose, row.bidhigh, row.bidlow, row.askopen, row.askclose, row.askhigh, row.asklow, row.tickqty, row.symbolid, row.timeframe))
                try:
                    print(f'{symbol_name} - {row.timeframe} - {i} - inserted ')
                except Exception as error:
                    print ("Oops! An exception has occured:", error)
                    print ("Exception TYPE:", type(error))
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))   

# Connection to postgresql
conn = db_connect() 
cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

## get instruments list
cur.execute("""
SELECT id, name FROM instruments WHERE market_id in (2,3,4) ORDER BY name
        """) 
instruments = cur.fetchall()

# FXCMapi connection
api = fxcm_connect()

# main program
previous_day = dt.datetime.today() - dt.timedelta(days=1)
now = dt.datetime.now()
current_hour = now.strftime("%H")
bars = 30
timeframes = ['H1']

#instruments = [(1, 'AUD/CAD')]

for instrument in instruments:
    print(f'Loading instrument....:{instrument[1]}')
    
    symbol_id, symbol_name = instrument 
    
    for timeframe in timeframes:
        
        try:
            historical_data = api.get_candles(symbol_name, period=timeframe, number=bars)
        except:
            print('historicaldataerror', historical_data)
            
            while historical_data is None:
                print('historical_data is None', historical_data)
                api.close()
                api = fxcm_connect()
                historical_data = api.get_candles(symbol_name, period=timeframe, number=bars)

        historical_data = historical_data.drop(historical_data.index[-1]) # drop current candle 
        historical_data['symbolid'] = symbol_id 
        historical_data['timeframe'] = timeframe

        if timeframe in ('H1', ):
            historical_data = historical_data.tz_localize(pytz.timezone('UTC'))
            historical_data = historical_data.tz_convert(pytz.timezone('Australia/Sydney'))
        
        try:
            DataframeToSql(historical_data)
        except Exception as error:
            print ("Oops! An exception has occured: dataframetosql", error)
            print ("Exception TYPE:", type(error))  

        historical_data = None
        
conn.commit()
api.close()

# call strategy scanner
ScanForStrategies() 
#UpdateNewTrade() - call from another file

conn.close()
