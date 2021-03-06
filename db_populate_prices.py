import psycopg2
import psycopg2.extras
import datetime as dt
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
                conn.commit()
                try:
                    print(f'{symbol_name} - {row.timeframe} - {i} - inserted ')
                except Exception as error:
                    print ("Oops! An exception has occured:", error)
                    print ("Exception TYPE:", type(error))
    except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))   

# Connection to postgresql
print('Connecting database:...')
conn = db_connect() 
cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

# main program
today = dt.datetime.today()
previous_day = today - dt.timedelta(days=1)
now = dt.datetime.now()
current_hour = now.strftime("%H") 
timeframes = ['D1','H1']
bars = 30

# 67 daily, 1355 hourly

for timeframe in timeframes:

    # get unprocessed instruments list for timeframe
    if timeframe == 'D1':
        if '00' <= current_hour <= '08':
            newdatetime = today - dt.timedelta(days=2)
            newdatetime = newdatetime.replace(hour=21, minute=00, second=00, microsecond=00)
        else:
            newdatetime = previous_day.replace(hour=21, minute=00, second=00, microsecond=00)
    else:
        if current_hour == '00':
            newdatetime = previous_day.replace(hour=23, minute=00, second=00, microsecond=00)
        else:
            previous_hour = int(current_hour) - 1
            newdatetime = today.replace(hour=previous_hour, minute=00, second=00, microsecond=00)       
    cur.execute("""
        SELECT 
            id_t, 
            name_t 
        FROM
            (SELECT id id_t, name name_t FROM instruments where market_id in (2,3,4)) as table1 
        LEFT JOIN 
            prices_fxcm_api on
            id_t = symbolid and 
            date >= %s and
            timeframe = %s 
        WHERE
            date is null
            """, (newdatetime, timeframe,)) 
    instruments = cur.fetchall()

    # loop through unprocessed items
    if instruments:
        try:
            print('Connecting api:...')
            api = fxcm_connect()    
            
            for instrument in instruments:
                
                symbol_id, symbol_name = instrument 
                print(f'Loading instrument....:{instrument[1]} - Timeframe: {timeframe}')
                
                try:

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

                    historical_data = None        
                    
                except:
                    print('historical data retrieve error for', symbol_name)
            api.close()

            # call strategy scanner
            ScanForStrategies() 
        except:
            print('failed to connect API')
    else:
        print('There is no new data to be uploaded!', timeframe)
    
conn.close()