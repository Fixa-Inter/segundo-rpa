TABELAS_MIGRADAS = {
    "super_administradores": "super_admin",
    "instituicoes": "instituicao",
    "planos": "plano",
    "unidades": "unidade",
    "usuarios": "usuario",
    "contratos": "contrato",
    "pagamentos": "pagamento",
    "fotos_usuario": "foto",
}


def selecionar_novos(dados, mapas):
    """Somente uma correspondência persistida prova que o registro já passou."""
    return {
        grupo: [registro for registro in dados[grupo]
                if registro["id"] not in mapas[grupo]]
        for grupo in TABELAS_MIGRADAS
    }
