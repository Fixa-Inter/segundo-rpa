def load_usuarios(conn, usuarios):
    query = """
        INSERT INTO usuario (
            id,
            endereco_id,
            nome_completo,
            email,
            tipo_acesso,
            senha_hash,
            cargo,
            data_nascimento,
            data_criacao,
            esta_ativo,
            primeiro_acesso
        )
        VALUES (
            %(id)s,
            %(endereco_id)s,
            %(nome_completo)s,
            %(email)s,
            %(tipo_acesso)s,
            %(senha_hash)s,
            %(cargo)s,
            %(data_nascimento)s,
            %(data_criacao)s,
            %(esta_ativo)s,
            %(primeiro_acesso)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, usuarios)