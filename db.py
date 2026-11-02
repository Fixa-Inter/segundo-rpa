import psycopg2
from config import db1ano_config, db2ano_config


def conectar_origem():
    try:
        return psycopg2.connect(**db1ano_config)
    except psycopg2.Error:
        raise ConnectionError("Não foi possível conectar ao banco de origem.") from None


def conectar_destino():
    try:
        return psycopg2.connect(**db2ano_config)
    except psycopg2.Error:
        raise ConnectionError("Não foi possível conectar ao banco de destino.") from None
