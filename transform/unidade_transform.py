def transform_unidades(unidades):

    unidades_transformadas = []

    for unidade in unidades:

        unidade_transformada = {
            "id": unidade["id"],
            "instituicao_id":unidade["fk_instituicao_id"],
            # Usa uma identificação por ID quando o nome da origem está vazio.
            "nome": unidade.get("nome") or f"Unidade {unidade['id']}",
            "cnpj": unidade["cnpj"],
            "logradouro": unidade["rua"],
            "numero": unidade["numero"],
            "complemento": unidade["complemento"],
            "bairro": unidade["bairro"],
            "cidade": unidade["cidade"],
            "estado": unidade["estado"],
            "cep": unidade["cep"],
            "data_criacao": unidade["data_criacao"]
        }

        unidades_transformadas.append(
            unidade_transformada
        )

    return unidades_transformadas
