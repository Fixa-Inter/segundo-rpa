from extract.instituicao_extract import extract_instituicoes
from extract.plano_extract import extract_planos
from extract.super_administrador_extract import extract_super_administradores
from extract.endereco_extract import extract_enderecos
from extract.usuario_extract import extract_usuarios
from extract.contrato_extract import extract_contratos
from extract.pagamento_extract import extract_pagamentos
from extract.foto_usuario_extract import extract_fotos_usuario


def extract_all():

    dados = {
        "instituicoes": extract_instituicoes(),
        "planos": extract_planos(),
        "super_administradores": extract_super_administradores(),
        "enderecos": extract_enderecos(),
        "usuarios": extract_usuarios(),
        "contratos": extract_contratos(),
        "pagamentos": extract_pagamentos(),
        "fotos_usuario": extract_fotos_usuario(),
    }

    return dados


if __name__ == "__main__":
    dados = extract_all()

    for tabela, registros in dados.items():
        print(
            f"{tabela}: {len(registros)} registros extraídos"
        )