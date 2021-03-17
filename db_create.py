from mlsc_utilities import db_connect

# Connection to postgresql
conn = db_connect()   
cur = conn.cursor()

# Database CREATE tables
try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS markets
    (
        id SERIAL UNIQUE, 
        name TEXT NOT NULL PRIMARY KEY
    ) 
    """)
    markets = ['New', 'Forex Major', 'Forex Minor', ' Forex Exotic', 'Index', 'Commodity', 'Crypto', 'Forex Basket' ]
    for market in markets:
        cur.execute("""
            INSERT INTO markets(name) VALUES (%s)
        """, (market,))        

    cur.execute("""
    CREATE TABLE IF NOT EXISTS instruments
    (
        id SERIAL UNIQUE, 
        name TEXT NOT NULL PRIMARY KEY,
        market_id INT REFERENCES markets(id),
        exchange TEXT NOT NULL
    ) 
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prices_fxcm_api
    (
        id serial NOT NULL PRIMARY KEY,
        date TIMESTAMPTZ NOT NULL,
        bidopen NUMERIC,
        bidclose NUMERIC,
        bidhigh NUMERIC,
        bidlow NUMERIC,
        askopen NUMERIC,
        askclose NUMERIC,
        askhigh NUMERIC,
        asklow NUMERIC,
        tickqty BIGINT,
        timeframe TEXT NOT NULL,
        symbolid INTEGER REFERENCES instruments(id)
    )
    """)

    # strategies 

    cur.execute("""
    CREATE TABLE IF NOT EXISTS strategies
    (
        id serial NOT NULL PRIMARY KEY,
        name TEXT NOT NULL
    )
    """)   

    strategies = ['breakout-1h-ema-50', ]
    for strategy in strategies:
        cur.execute("""
            INSERT INTO strategies(name) VALUES (%s)
        """, (strategy,))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS strategies_symbol
    (
        id serial NOT NULL PRIMARY KEY,
        symbol_id INTEGER NOT NULL REFERENCES instruments(id),
        strategy_id INTEGER NOT NULL REFERENCES strategies(id),
        strategy_bias TEXT NOT NULL,
        date TIMESTAMPTZ NOT NULL,
        entry_point NUMERIC,
        stop_loss NUMERIC,
        take_profit NUMERIC,        
        status TEXT NOT NULL,
        trade_id INT 
    )
    """)   

    conn.commit()
    conn.close()
except Exception as error:
    print ("Oops! An exception has occured:", error)
    print ("Exception TYPE:", type(error))   