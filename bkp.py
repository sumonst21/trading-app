import sqlite3
import fxcmpy
import socketio

connection = sqlite3.connect('trading_app.db')
connection.row_factory = sqlite3.Row
cursor = connection.cursor()


cursor.execute("""
    SELECT id, symbol FROM instruments
""")

rows = cursor.fetchall()
symbols = []
stock_dict = {}

for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    instrument_dict[symbol] = row['id']
    api = fxcmpy.fxcmpy(config_file='fxcm.cfg') 
    chunk_size = 200

for i in range(0, len(symbols), chunk_size):
    symbol_chunk = symbols[i:i+chunk_size]
    barsets = api.get_candles(symbol_chunk, period='D1')  # daily data
    for symbol in barsets:
        print(f"processing symbol {symbol}")
        for bar in barsets[symbol]:
            instrument_id = instrument_dict[symbol]
            cursor.execute("""
                INSERT INTO prices (instrument_id, date, bidopen, bidclose, bidhigh   bidlow  askopen  askclose  askhigh   asklow  tickqty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v))

connection.commit()

