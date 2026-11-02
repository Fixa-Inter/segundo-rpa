def load_planos(conn, planos):
    query = """
        INSERT INTO plano (
            id,
            nome,
            valor,
            descricao,
            duracao_meses,
            data_criacao
        )
        VALUES (
            %(id)s,
            %(nome)s,
            %(valor)s,
            %(descricao)s,
            %(duracao_meses)s,
            %(data_criacao)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, planos)