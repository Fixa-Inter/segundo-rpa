def transform_super_administradores(super_administradores):

    administradores_transformados = []

    for administrador in super_administradores:

        administrador_transformado = {
            "id": administrador["id"],
            "nome": administrador["nome"],
            "email": administrador["email"],
            "senha_hash": administrador["senha_hash"]
        }

        administradores_transformados.append(
            administrador_transformado
        )

    return administradores_transformados