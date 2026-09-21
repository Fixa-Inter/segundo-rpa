def load_fotos_usuario(conn, fotos_usuario):
    query = """
        INSERT INTO foto (
            id,
            usuario_id,
            url,
            data_criacao
        )
        VALUES (
            %(id)s,
            %(usuario_id)s,
            %(url)s,
            %(data_criacao)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, fotos_usuario)