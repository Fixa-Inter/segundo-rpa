from contextlib import closing

from db import conectar_origem


def extract_instituicoes():

    query = """
        SELECT
            id,
            nome,
            email_corporativo,
            data_cadastro,
            dominio_email,
            tipo_instituicao
        FROM instituicao
        ORDER BY id;
    """

    conn = conectar_origem()

    if conn is None:
        raise ConnectionError(
            "Não foi possível conectar ao banco de origem."
        )

    with closing(conn):
        with conn.cursor() as cursor:

            cursor.execute(query)

            columns = [
                description[0]
                for description in cursor.description
            ]

            rows = cursor.fetchall()

            return [
                dict(zip(columns, row))
                for row in rows
            ]