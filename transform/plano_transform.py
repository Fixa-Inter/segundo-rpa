def transform_planos(planos):

    planos_transformados = []

    for plano in planos:

        if plano["valor_mensal"] < 0:
            raise ValueError(
                f"Valor inválido no plano {plano['id']}"
            )

        if plano["duracao_meses"] <= 0:
            raise ValueError(
                f"Duração inválida no plano {plano['id']}"
            )

        plano_transformado = {
            "id": plano["id"],
            "nome": plano["nome"],
            "valor": plano["valor_mensal"],
            "descricao": plano["descricao"],
            "duracao_meses": plano["duracao_meses"],
            "data_criacao": plano["data_criacao"]
        }

        planos_transformados.append(
            plano_transformado
        )

    return planos_transformados