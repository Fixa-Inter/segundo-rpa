import psycopg2
from config import db1ano_config, db2ano_config 

def conectar_origem():
    try: 
        conn = psycopg2.connect(**db1ano_config)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to origin database: {e}")
        return None
    finally:
        if conn:
            conn.close()

def conectar_destino():
    try:
        conn = psycopg2.connect(**db2ano_config)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to destination database: {e}")
        return None
    finally:
        if conn:
            conn.close()