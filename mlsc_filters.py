import psycopg2
import psycopg2.extras
from mlsc_utilities import db_connect, get_instruments_list

# db connection
conn = db_connect()
cur = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

# filter candle_sequence
# find instruments with sequence of five or ore candle-stick of same colour (red or green)

