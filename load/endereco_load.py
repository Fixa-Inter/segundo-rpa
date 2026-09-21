def load_enderecos(conn, enderecos):
    query = """
        INSERT INTO endereco (
            id,
            instituicao_id,
            cnpj,
            logradouro,
            numero,
            complemento,
            bairro,
            cidade,
            estado,
            cep,
            data_criacao
        )
        VALUES (
            %(id)s,
            %(instituicao_id)s,
            %(cnpj)s,
            %(logradouro)s,
            %(numero)s,
            %(complemento)s,
            %(bairro)s,
            %(cidade)s,
            %(estado)s,
            %(cep)s,
            %(data_criacao)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, enderecos)