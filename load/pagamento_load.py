def load_pagamentos(conn, pagamentos):
    query = """
        INSERT INTO pagamento (
            id,
            contrato_id,
            data_pagamento,
            valor_pago,
            status,
            metodo_pagamento,
            data_criacao
        )
        VALUES (
            %(id)s,
            %(contrato_id)s,
            %(data_pagamento)s,
            %(valor_pago)s,
            %(status)s,
            %(metodo_pagamento)s,
            %(data_criacao)s
        );
    """

    with conn.cursor() as cursor:
        cursor.executemany(query, pagamentos)