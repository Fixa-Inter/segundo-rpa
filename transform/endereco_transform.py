def transform_enderecos(enderecos):

    enderecos_transformados = []

    for endereco in enderecos:

        endereco_transformado = {
            "id": endereco["id"],
            "instituicao_id":endereco["fk_instituicao_id"],
            "cnpj": endereco["cnpj"],
            "logradouro": endereco["rua"],
            "numero": endereco["numero"],
            "complemento": endereco["complemento"],
            "bairro": endereco["bairro"],
            "cidade": endereco["cidade"],
            "estado": endereco["estado"],
            "cep": endereco["cep"],
            "data_criacao": endereco["data_criacao"]
        }

        enderecos_transformados.append(
            endereco_transformado
        )

    return enderecos_transformados