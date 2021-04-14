from mlsc_utilities import db_connect

# Connection to postgresql
conn = db_connect()  
cursor = conn.cursor()

# Database DROP tables
try:

    cursor.execute("""
        DROP TABLE IF EXISTS exchanges
    """)    

    cursor.execute("""
        DROP TABLE IF EXISTS alerts_symbol
    """)

    cursor.execute("""
        DROP TABLE IF EXISTS alerts
    """)

    cursor.execute("""
        DROP TABLE IF EXISTS strategies_symbol
    """)

    cursor.execute("""
        DROP TABLE IF EXISTS strategies
    """)

    cursor.execute("""
        DROP TABLE IF EXISTS prices_fxcm_api
    """)

    cursor.execute("""
        DROP TABLE IF EXISTS instruments
    """)

    cursor.execute("""
        DROP TABLE IF EXISTS markets
    """)

    conn.commit()
    conn.close()   
except Exception as error:
        print ("Oops! An exception has occured:", error)
        print ("Exception TYPE:", type(error))   




