import psycopg2, psycopg2.extras
from config import configdb
import backtrader, pandas as pd, sqlite3, pytz
from datetime import date, datetime, time, timedelta
from mlsc_utilities import db_connect, postgresql_to_dataframe, get_instruments_list


class breakout_1h_ema_50(backtrader.Strategy):
#     params = dict(
#         daily_bias=''
#     )

    def __init__(self):
        self.hourlyclose = self.datas[0].close
        self.hourlyopen = self.datas[0].open
        self.hourlylow = self.datas[0].low
        self.hourlyhigh = self.datas[0].high
        
        self.dailyclose = self.data1.close
        self.dailyopen = self.data1.open
        self.dailylow = self.data1.low
        self.dailyhigh = self.data1.high
        
        self.lendata1 = 0

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def next(self):

        self.current_hourly_bar = self.data.num2date(self.data.datetime[0])
        self.previous_hourly_bar = self.data.num2date(self.data.datetime[-1])

        # loop through D1 timeframe
        
        self.current_daily_bar = self.data1.num2date(self.data1.datetime[0])
        print('current_hourly_bar', self.current_hourly_bar, self.current_daily_bar  )


            # print('current_hourly_bar', self.current_hourly_bar,
            #     'close_price', self.hourlyclose[0], 
            #     'open price', self.hourlyopen[0], 
            #     'lowprice', self.hourlylow[0], 
            #     'highprice', self.hourlyhigh[0],
            #     'dailyopen:', self.dailyopen[0])

         

if __name__ == '__main__':
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    params = configdb()
        
    symbols = get_instruments_list((2,3,4,))
    symbols = [('AUD/USD', 685)]


    for symbol in symbols:

        symbol_name, symbol_id = symbol
        print(f"== Testing {symbol_name} ==")

        cerebro = backtrader.Cerebro()
        cerebro.broker.setcash(100000.0)
        # cerebro.addsizer(backtrader.sizers.PercentSizer, percents=95)

        # getting dataframe H1 from database
        select_query = """
            SELECT 
                date,
                bidopen,
                bidhigh,
                bidlow,
                bidclose,
                timeframe
            FROM
                prices_fxcm_api
            WHERE
                timeframe = 'H1'
            and symbolid = %s 
            and date >= '2021-01-05'
            and date <= '2021-03-19' 
            order by date asc
        """ 
        params = [symbol_id,]
        column_names =  ['date', 'open', 'high', 'low', 'close', 'timeframe']
        dataframe = postgresql_to_dataframe(conn, select_query, params, column_names)
        dataframe['date'] = pd.to_datetime(dataframe['date']).dt.tz_convert(None) 
        dataframe.set_index('date', inplace=True)  
              # supplying data H1 to backtrader
        data = backtrader.feeds.PandasData(dataname=dataframe, tz=pytz.timezone('Australia/Sydney'))

        
        cerebro.adddata(data)
        
        # generating daily timeframe data        
        cerebro.resampledata(data, timeframe = backtrader.TimeFrame.Days, compression = 1)
        cerebro.addstrategy(breakout_1h_ema_50)
    
        #strats = cerebro.optstrategy(breakout_1h_ema_50, daily_bias=['Long', 'Short'])
        # Print out the starting conditions
        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # Run over everything
        cerebro.run()

        # Print out the final result
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
            
             
 
        #cerebro.plot()
