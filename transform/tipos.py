def texto_varchar(valor, limite, campo, registro_id, *, remover_padding=False):
    """Validate SQL text without truncating it or losing leading zeros."""
    if not isinstance(valor, str):
        raise ValueError(
            f"{campo} no registro {registro_id}: esperado texto, "
            f"recebido {type(valor).__name__}"
        )

    if remover_padding:
        valor = valor.rstrip(" ")

    if len(valor) > limite:
        raise ValueError(
            f"{campo} no registro {registro_id}: "
            f"{len(valor)} caracteres excedem VARCHAR({limite})"
        )

    return valor
