def load_instituicoes(conn, instituicoes):
    query = """
        INSERT INTO instituicao (
            id,
            nome,
            tipo_instituicao,
            email_corporativo,
            dominio_email,
            data_criacao
        )
        VALUES (
            %(id)s,
            %(nome)s,
            %(tipo_instituicao)s,
            %(email_corporativo)s,
            %(dominio_email)s,
            %(data_criacao)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, instituicoes)