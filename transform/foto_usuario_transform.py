def transform_fotos_usuario(fotos):

    fotos_transformadas = []

    for foto in fotos:

        foto_transformada = {
            "id": foto["id"],
            "usuario_id":foto["fk_usuario_id"],
            "url":foto["url"],
            "data_criacao":foto["data_registro"]
        }

        fotos_transformadas.append(
            foto_transformada
        )

    return fotos_transformadas