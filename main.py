from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import psycopg2 
import psycopg2.extras
from config import configdb
from datetime import date
from mlsc_utilities import db_connect

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def index(request: Request):
    symbol_filters = request._query_params.get('filter', False)

    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    if symbol_filters == 'new_close_highs':
        cursor.execute("""
            select 
            	symbolid as id, 
                maxname as name 
            from
            	(SELECT 
            		t2.id as maxid,
            		t2.name as maxname,
            		max(bidclose) as maxclose
            	FROM 
            		prices_fxcm_api t1
            	JOIN
            		instruments t2 ON t2.id = t1.symbolid
            	GROUP BY
            		t2.name
            	ORDER BY
            		t2.id) as t1
            JOIN prices_fxcm_api t2 on
            	maxid = symbolid
            WHERE
                t2.date = %s
            GROUP BY
	            symbolid, maxname
            ORDER BY 
            	symbolid
        """, (date.today().isoformat(),))   
    else:
        cursor.execute("""
            SELECT 
			    t1.id id, 
		   	    t1.name assetname, 
		   	    t2.name marketname, 
		   	    exchange 
	        FROM 
			    instruments t1, 
			    markets t2 
	        WHERE 
			    t1.market_id = t2.id and
                t1.market_id <> 1
	        ORDER BY 
			    t1.market_id, t1.name 
        """)    
    
    rows = cursor.fetchall()

    return templates.TemplateResponse("index.html", {"request": request, "symbols": rows})

@app.get("/asset/{symbolid}")
def symbol_details(request: Request, symbolid):

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

    return templates.TemplateResponse("symbol_details.html", {"request": request, "prices": rows, "symbolid": symbolid, "symbolname": symbolname, "strategies": strategies })
 
@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), symbolid: int = Form(...), strategy_bias: str = Form(...), ):
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

@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
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
            t1.strategy_id = %s
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
def index(request: Request):
    
    conn = db_connect()
    cursor = conn.cursor(cursor_factory = psycopg2.extras.DictCursor)

    cursor.execute("""
        SELECT id, name FROM strategies
    """)
    
    rows = cursor.fetchall()

    return templates.TemplateResponse("strategies.html", {"request": request, "strategies": rows})


