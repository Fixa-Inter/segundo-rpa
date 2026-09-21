def transform_usuarios(usuarios):

    usuarios_transformados = []

    tipos_acesso_validos = [1, 2, 3, 4]

    for usuario in usuarios:

        if usuario["tipo_de_acesso"] not in tipos_acesso_validos:
            raise ValueError(
                f"Tipo de acesso inválido no usuário "
                f"{usuario['id']}: "
                f"{usuario['tipo_de_acesso']}"
            )

        usuario_transformado = {
            "id": usuario["id"],

            "endereco_id":
                usuario["fk_endereco_id"],

            "nome_completo":
                usuario["nome"],

            "email": usuario["email"],

            "tipo_acesso":
                usuario["tipo_de_acesso"],

            "senha_hash": usuario["senha_hash"],
            "cargo": usuario["cargo"],
            "data_nascimento":
                usuario["data_nascimento"],

            "data_criacao":
                usuario["data_criacao"],

            "esta_ativo":
                usuario["esta_ativo"],

            "primeiro_acesso":
                usuario["primeiro_acesso"]
        }

        usuarios_transformados.append(
            usuario_transformado
        )

    return usuarios_transformados