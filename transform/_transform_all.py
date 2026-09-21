from transform.instituicao_transform import transform_instituicoes
from transform.endereco_transform import transform_enderecos
from transform.plano_transform import transform_planos
from transform.super_administrador_transform import transform_super_administradores
from transform.usuario_transform import transform_usuarios
from transform.contrato_transform import transform_contratos
from transform.pagamento_transform import transform_pagamentos
from transform.foto_usuario_transform import transform_fotos_usuario


def transform_all(dados_extraidos):
    dados_transformados = {
        "instituicoes": transform_instituicoes(dados_extraidos["instituicoes"]),
        "enderecos": transform_enderecos(dados_extraidos["enderecos"]),
        "planos": transform_planos(dados_extraidos["planos"]),
        "super_administradores": transform_super_administradores(
            dados_extraidos["super_administradores"]
        ),
        "usuarios": transform_usuarios(dados_extraidos["usuarios"]),
        "contratos": transform_contratos(dados_extraidos["contratos"]),
        "pagamentos": transform_pagamentos(dados_extraidos["pagamentos"]),
        "fotos_usuario": transform_fotos_usuario(dados_extraidos["fotos_usuario"])
    }

    return dados_transformados