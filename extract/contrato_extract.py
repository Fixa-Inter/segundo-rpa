from contextlib import closing

from db import conectar_origem


def extract_contratos():

    query = """
        SELECT
            id,
            data_inicio,
            data_vencimento,
            fk_plano_id,
            fk_endereco_id,
            status,
            data_criacao
        FROM contrato
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