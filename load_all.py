from contextlib import closing

from db import conectar_destino

from load.super_administrador_load import load_super_administradores
from load.instituicao_load import load_instituicoes
from load.plano_load import load_planos
from load.endereco_load import load_enderecos
from load.usuario_load import load_usuarios
from load.contrato_load import load_contratos
from load.pagamento_load import load_pagamentos
from load.foto_usuario_load import load_fotos_usuario
from load.sequence import ajustar_sequences


def load_all(dados_transformados):
    conn = conectar_destino()

    with closing(conn):
        with conn:
            load_super_administradores(
                conn,
                dados_transformados["super_administradores"]
            )

            load_instituicoes(
                conn,
                dados_transformados["instituicoes"]
            )

            load_planos(
                conn,
                dados_transformados["planos"]
            )

            load_enderecos(
                conn,
                dados_transformados["enderecos"]
            )

            load_usuarios(
                conn,
                dados_transformados["usuarios"]
            )

            load_contratos(
                conn,
                dados_transformados["contratos"]
            )

            load_pagamentos(
                conn,
                dados_transformados["pagamentos"]
            )

            load_fotos_usuario(
                conn,
                dados_transformados["fotos_usuario"]
            )

            ajustar_sequences(conn)