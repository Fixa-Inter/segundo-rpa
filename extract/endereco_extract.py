from db import conectar_origem

def extract_enderecos():
    query = """
        SELECT
            id,
            rua,
            bairro,
            complemento,
            cidade,
            estado,
            numero,
            cep,
            fk_instituicao_id,
            cnpj,
            data_criacao
        FROM endereco
    ORDER BY id;
    """

    conn = conectar_origem()
    cursor = conn.cursor()

    try:
        with cursor:
            cursor.execute(query)

            columns = [
                description[0]
                for description in cursor.description
            ]

            rows = cursor.fetchall()

            enderecos = [
                dict(zip(columns, row))
                for row in rows
            ]

            return enderecos

    finally:
        conn.close()