from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import psycopg2 
import psycopg2.extras
from config import configdb, configemail
from datetime import date
from mlsc_utilities import db_connect, sql_count, get_market_list, get_exchange_list


# Fast API - Initial Load
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# path operation decorators
@app.get("/")
async def index(request: Request):

    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    exchanges = sql_count("exchanges")
    strategies = sql_count("strategies")
    trades = sql_count("strategies_symbol")
    instruments = sql_count("instruments")

    return templates.TemplateResponse("index.html", {"request": request, "exchanges": exchanges, "strategies": strategies, "trades": trades, "instruments": instruments})

@app.get("/exchanges")
async def exchanges(request: Request):
    
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    cursor.execute("""
        SELECT
            id,
            exchange
        FROM
            exchanges
    """)
    rows = cursor.fetchall()
    return templates.TemplateResponse("exchanges.html", {"request": request, "exchanges": rows})

@app.get("/settings")
async def settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/instruments/p/{page}")
async def instrument(request: Request, page):
    markets = get_market_list()
    instrument_filters = request._query_params.get('filter', False) 
    
    # Pagination
    page_current = int(page)
    records_per_page = 15
    offset = (page_current - 1) * records_per_page

    # Database
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    # Filters

    cursor.execute("""
        SELECT 
            count(*)
        FROM
            instruments
        WHERE 
            market_id <> 1
    """)
    total_pages = cursor.fetchone()
    total_pages = round(total_pages[0]  / records_per_page)
    
    cursor.execute("""
        SELECT 
            t1.name, 
            t1.id id, 
            t2.name market, 
            t3.exchange 
        FROM 
            instruments t1, 
            markets t2,
			exchanges t3
        WHERE 
            t1.market_id = t2.id and
            t1.market_id <> 1 and
			cast(t1.exchange as int) = t3.id
        ORDER BY 
            t1.market_id, t1.name 
        LIMIT %s
        OFFSET %s
    """, (records_per_page, offset,))    
    rows = cursor.fetchall()

    pagination = {"page_current": page_current, "records_per_page": records_per_page, "offset": offset }

    return templates.TemplateResponse("instruments.html", {"request": request, "instruments": rows, "total_pages": total_pages, "pagination": pagination, "markets": markets})

@app.get("/strategy/{strategy_id}")
async def strategy(request: Request, strategy_id):
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)
    
    cursor.execute("""
        SELECT 
            t1.id, 
            t1.symbol_id, 
            t1.strategy_id,
            t2.name,
            t1.strategy_bias,
            t1.entry_point,
            t1.stop_loss,
            t1.take_profit,
            t1.date,
            t1.status
        FROM
            strategies_symbol t1,
            instruments t2
        WHERE
            t1.symbol_id = t2.id and 
            t1.strategy_id = %s and
            t1.status in ('new', 'trading')
        ORDER by
            t1.status
    """, (strategy_id,))

    strategies = cursor.fetchall()

    cursor.execute("""
                SELECT 
                    name
                FROM
                    strategies_symbol t1,
                    strategies t2
                WHERE
                    t1.strategy_id = t2.id and 
                    t1.strategy_id = %s
                GROUP BY
                    name
    """, (strategy_id,))
    strategy_name = cursor.fetchone()['name']

    return templates.TemplateResponse("strategy.html", {"request": request, "strategies": strategies, "strategy_name": strategy_name })

@app.get("/strategies")
async def strategies(request: Request):
    
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    cursor.execute("""
        SELECT id, name FROM strategies
    """)
    
    rows = cursor.fetchall()

    return templates.TemplateResponse("strategies.html", {"request": request, "strategies": rows})

@app.get("/instrument/{symbolid}")
async def symbol_details(request: Request, symbolid):

    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    # get symbol name
    cursor.execute("""
        SELECT name FROM instruments WHERE id = %s
    """, (symbolid,))
    row = cursor.fetchone()['name']
    symbolname = row.replace('/', '')

    # get symbol price list
    cursor.execute("""
        SELECT 
            date, 
            timeframe, 
            bidopen, 
            bidclose, 
            bidhigh, 
            bidlow, 
            symbolid,
            name 
        FROM 
            prices_fxcm_api,
            instruments 
        WHERE 
            instruments.id = symbolid and
            symbolid = %s
        ORDER BY
            timeframe,
            date desc
    """, (symbolid,))
    rows = cursor.fetchall()

    # get strategies list
    cursor.execute("""
        SELECT id, name FROM strategies
    """)   
    strategies = cursor.fetchall()

    return templates.TemplateResponse("instrument_details.html", {"request": request, "prices": rows, "symbolid": symbolid, "symbolname": symbolname, "strategies": strategies })
 
@app.get("/instruments/new")
async def intruments_new(request: Request):

    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    markets = get_market_list()

    exchanges = get_exchange_list()

    return templates.TemplateResponse("instruments_new.html", {"request": request, "markets": markets, "exchanges": exchanges })

@app.post("/create_instrument")
async def create_instrument(request: Request, symbol: str = Form(...), market_id: int = Form(...), exchange_id: int = Form(...) ):

    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    sql = "INSERT INTO instruments(name, market_id, exchange) VALUES (%s, %s, %s);"
    cursor.execute(sql, (symbol, market_id, exchange_id,))
    conn.commit()
    message = f'New instrument created {symbol}'

    return templates.TemplateResponse("message_create.html", {"request": request, "message": message })

@app.post("/apply_strategy")
async def apply_strategy(strategy_id: int = Form(...), symbolid: int = Form(...), strategy_bias: str = Form(...), ):
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    # check for existent symbol_strategies rows
    cursor.execute("""
        SELECT 
            t1.id, 
            t1.symbol_id, 
            t1.strategy_id,
            t2.name
        FROM
            strategies_symbol t1,
            instruments t2
        WHERE
            t1.symbol_id = t2.id and 
            t1.strategy_id = %s and
			t1.symbol_id = %s and
            t1.status = 'new'
    """, (strategy_id, symbolid))
    
    strategy = cursor.fetchone()

    if not strategy:
        cursor.execute("""
            INSERT INTO strategies_symbol( symbol_id, strategy_id, strategy_bias, entry_point, stop_loss, take_profit, date, status ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (symbolid, strategy_id, strategy_bias, 0, 0, 0, date.today(), 'new', ))

        conn.commit() 

        return RedirectResponse(url=f"/strategy/{strategy_id}", status_code = 303)

@app.post("/delete_instrument/{trading_id}")
async def delete_instrument(request: Request, trading_id):
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    cursor.execute("""
        DELETE FROM strategies_symbol WHERE id = %s
    """, (trading_id,))
    conn.commit()

    message = f'Trading deleted {trading_id}'

    if Response(status_code=200):
        return templates.TemplateResponse("message_create.html", {"request": request, "message": message })

@app.get("/login")
async def user_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})