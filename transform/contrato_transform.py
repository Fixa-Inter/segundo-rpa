def transform_contratos(contratos):

    contratos_transformados = []

    status_validos = [1, 2, 3]

    for contrato in contratos:

        if contrato["status"] not in status_validos:
            raise ValueError(
                f"Status inválido no contrato "
                f"{contrato['id']}: "
                f"{contrato['status']}"
            )

        if contrato["data_vencimento"] <= contrato["data_inicio"]:
            raise ValueError(
                f"Datas inválidas no contrato "
                f"{contrato['id']}"
            )

        contrato_transformado = {
            "id": contrato["id"],

            "plano_id":
                contrato["fk_plano_id"],

            "endereco_id":
                contrato["fk_endereco_id"],

            "data_inicio":
                contrato["data_inicio"],

            "data_fim":
                contrato["data_vencimento"],

            "status":
                contrato["status"],

            "data_criacao":
                contrato["data_criacao"]
        }

        contratos_transformados.append(
            contrato_transformado
        )

    return contratos_transformados