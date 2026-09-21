import os
from dotenv import load_dotenv

load_dotenv()

db1ano_config = {
    "host": os.getenv("LEGADO_HOST"),
    "port": os.getenv("LEGADO_PORT"),
    "dbname": os.getenv("LEGADO_NAME"),
    "user": os.getenv("LEGADO_USER"),
    "password": os.getenv("LEGADO_PASS"),
    "sslmode": "require",
}

db2ano_config = {
    "host": os.getenv("NORM_HOST"),
    "port": os.getenv("NORM_PORT"),
    "dbname": os.getenv("NORM_NAME"),
    "user": os.getenv("NORM_USER"),
    "password": os.getenv("NORM_PASS"),
    "sslmode": "require",
}