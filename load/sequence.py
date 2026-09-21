def ajustar_sequence_id(conn, tabela):
    query = f"""
        SELECT setval(
            pg_get_serial_sequence('{tabela}', 'id'),
            COALESCE(MAX(id), 1)
        )
        FROM {tabela};
    """

    with conn.cursor() as cursor:
        cursor.execute(query)


def ajustar_sequences(conn):
    tabelas = [
        "super_admin",
        "instituicao",
        "plano",
        "endereco",
        "usuario",
        "contrato",
        "pagamento",
        "foto"
    ]

    for tabela in tabelas:
        ajustar_sequence_id(conn, tabela)