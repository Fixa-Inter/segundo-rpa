def transform_instituicoes(instituicoes):

    instituicoes_transformadas = []

    tipos_validos = [1, 2, 3, 4]

    for instituicao in instituicoes:

        if instituicao["tipo_instituicao"] not in tipos_validos:
            raise ValueError(
                f"Tipo de instituição inválido no registro "
                f"{instituicao['id']}: "
                f"{instituicao['tipo_instituicao']}"
            )

        instituicao_transformada = {
            "id": instituicao["id"],
            "nome": instituicao["nome"],
            "tipo_instituicao": instituicao["tipo_instituicao"],
            "email_corporativo": instituicao["email_corporativo"],
            "dominio_email": instituicao["dominio_email"],
            "data_criacao": instituicao["data_cadastro"]
        }

        instituicoes_transformadas.append(
            instituicao_transformada
        )

    return instituicoes_transformadas