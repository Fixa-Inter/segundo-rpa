from contextlib import closing

from db import conectar_origem


def extract_usuarios():

    query = """
        SELECT
            id,
            nome,
            senha_hash,
            esta_ativo,
            email,
            data_criacao,
            cargo,
            tipo_de_acesso,
            fk_endereco_id,
            gerente_id,
            data_nascimento,
            primeiro_acesso
        FROM usuario
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