from transform.tipos import texto_varchar


def transform_unidades(unidades):

    unidades_transformadas = []

    for unidade in unidades:

        unidade_transformada = {
            "id": unidade["id"],
            "instituicao_id":unidade["fk_instituicao_id"],
            # Usa uma identificação por ID quando o nome da origem está vazio.
            "nome": texto_varchar(unidade.get("nome") or f"Unidade {unidade['id']}", 100, "nome", unidade["id"]),
            "cnpj": texto_varchar(unidade["cnpj"], 14, "cnpj", unidade["id"], remover_padding=True),
            "logradouro": texto_varchar(unidade["rua"], 100, "logradouro", unidade["id"]),
            "numero": texto_varchar(unidade["numero"], 10, "numero", unidade["id"]),
            "complemento": (
                texto_varchar(unidade["complemento"], 100, "complemento", unidade["id"])
                if unidade["complemento"] is not None else None
            ),
            "bairro": texto_varchar(unidade["bairro"], 100, "bairro", unidade["id"]),
            "cidade": texto_varchar(unidade["cidade"], 100, "cidade", unidade["id"]),
            "estado": texto_varchar(unidade["estado"], 2, "estado", unidade["id"], remover_padding=True),
            "cep": texto_varchar(unidade["cep"], 8, "cep", unidade["id"], remover_padding=True),
            "data_criacao": unidade["data_criacao"]
        }

        unidades_transformadas.append(
            unidade_transformada
        )

    return unidades_transformadas
