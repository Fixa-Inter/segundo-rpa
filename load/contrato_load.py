def load_contratos(conn, contratos):
    query = """
        INSERT INTO contrato (
            id,
            plano_id,
            endereco_id,
            data_inicio,
            data_fim,
            status,
            data_criacao
        )
        VALUES (
            %(id)s,
            %(plano_id)s,
            %(endereco_id)s,
            %(data_inicio)s,
            %(data_fim)s,
            %(status)s,
            %(data_criacao)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, contratos)