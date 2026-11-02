def transform_pagamentos(pagamentos):

    pagamentos_transformados = []

    metodos_validos = [1, 2, 3]

    for pagamento in pagamentos:

        if pagamento["valor"] < 0:
            raise ValueError(
                f"Valor inválido no pagamento "
                f"{pagamento['id']}"
            )

        if (
            pagamento["metodo_pagamento"]
            not in metodos_validos
        ):
            raise ValueError(
                f"Método de pagamento inválido no "
                f"pagamento {pagamento['id']}"
            )

        if pagamento["foi_realizado"] is True:
            status = 2

        elif pagamento["foi_realizado"] is False:
            status = 1

        else:
            raise ValueError(
                f"foi_realizado inválido no pagamento "
                f"{pagamento['id']}"
            )

        pagamento_transformado = {
            "id": pagamento["id"],

            "contrato_id":
                pagamento["fk_contrato_id"],

            "data_pagamento":
                pagamento["data_pagamento"],

            "valor_pago":
                pagamento["valor"],

            "status":
                status,

            "metodo_pagamento":
                pagamento["metodo_pagamento"],

            "data_criacao":
                pagamento["data_criacao"]
        }

        pagamentos_transformados.append(
            pagamento_transformado
        )

    return pagamentos_transformados