def load_unidades(conn, unidades):
    query = """
        INSERT INTO unidade (
            id,
            instituicao_id,
            nome,
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
            %(nome)s,
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
        cursor.executemany(query, unidades)
