from contextlib import closing
import sys

import psycopg2

from relatorio import Relatorio
from db import conectar_destino
from extract._extract_all import extract_all
from transform._transform_all import transform_all
from load._load_all import load_all
from load.validacao import selecionar_novos
from load.correspondencia import Correspondencia, CorrespondenciaAmbigua


# Também impede sobreposição entre execução manual/local e GitHub Actions.
CHAVE_LOCK_RPA = 824167


def main():
    relatorio = Relatorio()
    relatorio.salvar()
    try:
        relatorio.etapa("conectando_destino")
        with closing(conectar_destino()) as conn:
            with conn:
                relatorio.dados["transacao"] = "aberta"
                relatorio.etapa("obtendo_bloqueio")
                with conn.cursor() as cursor:
                    cursor.execute("SELECT pg_try_advisory_xact_lock(%s)", (CHAVE_LOCK_RPA,))
                    if not cursor.fetchone()[0]:
                        relatorio.dados["transacao"] = "sem_insercoes"
                        relatorio.finalizar("ignorada")
                        print("Outra sincronização já está em execução; rodada ignorada.")
                        return {}
                relatorio.etapa("extraindo")
                dados_extraidos = extract_all()
                for grupo, registros in dados_extraidos.items():
                    relatorio.dados["tabelas"][grupo]["extraidos"] = len(registros)
                relatorio.etapa("identificando_novos")
                controle = Correspondencia(conn)
                controle.preparar()
                mapas = controle.carregar()
                novos = selecionar_novos(dados_extraidos, mapas)
                for grupo, registros in novos.items():
                    valores = relatorio.dados["tabelas"][grupo]
                    valores["candidatos"] = len(registros)
                    valores["ja_mapeados"] = valores["extraidos"] - len(registros)
                relatorio.etapa("validando_transformando")
                ids_origem_mapeados = {grupo: set(mapa) for grupo, mapa in mapas.items()}
                dados_transformados = transform_all(novos, ids_origem_mapeados)
                relatorio.etapa("conciliando_carregando")
                controle.bloquear_tabelas()
                controle.verificar()
                totais = load_all(controle, dados_transformados, mapas)
                resumo = {grupo: valores["inseridos"] for grupo, valores in totais.items()}
                relatorio.etapa("confirmando_transacao")
            # O contexto da conexão confirmou o commit.
            relatorio.dados["transacao"] = "confirmada"
            for grupo, total in resumo.items():
                relatorio.dados["tabelas"][grupo]["inseridos_confirmados"] = total
                relatorio.dados["tabelas"][grupo]["conciliados"] = totais[grupo]["conciliados"]
            relatorio.finalizar("sucesso" if sum(resumo.values()) else "sem_novidades")
        print("Sincronização concluída. Novos registros por grupo:", resumo)
        return resumo
    except Exception as erro:
        if relatorio.dados["transacao"] != "confirmada":
            incerto = relatorio.dados["etapa"] == "confirmando_transacao"
            relatorio.dados["transacao"] = "resultado_nao_confirmado" if incerto else "sem_commit_confirmado"
            for valores in relatorio.dados["tabelas"].values():
                valores["inseridos_confirmados"] = None if incerto else 0
        if isinstance(erro, CorrespondenciaAmbigua):
            relatorio.dados["ambiguidades"].append(erro.detalhes)
        relatorio.dados["erro"] = {
            "categoria": ("ambiguidade" if isinstance(erro, CorrespondenciaAmbigua)
                          else "banco" if isinstance(erro, psycopg2.Error)
                          else "validacao" if isinstance(erro, ValueError)
                          else "conexao" if isinstance(erro, ConnectionError) else "inesperado"),
            "sqlstate": getattr(erro, "pgcode", None),
        }
        relatorio.finalizar("falha")
        raise


if __name__ == "__main__":
    try:
        main()
    except psycopg2.Error as erro:
        # Não exibe o DETAIL do PostgreSQL, que pode conter dados de uma linha.
        print(f"Sincronização cancelada por erro no banco (SQLSTATE {erro.pgcode or 'indisponível'}).", file=sys.stderr)
        sys.exit(1)
    except (ValueError, ConnectionError) as erro:
        print(str(erro), file=sys.stderr)
        sys.exit(1)
