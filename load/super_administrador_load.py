def load_super_administradores(conn, super_administradores):
    query = """
        INSERT INTO super_admin (
            id,
            nome,
            email,
            senha_hash
        )
        VALUES (
            %(id)s,
            %(nome)s,
            %(email)s,
            %(senha_hash)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, super_administradores)