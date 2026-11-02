from load.validacao import TABELAS_MIGRADAS
from load.correspondencia import remapear_vinculos


def load_all(controle, dados_transformados, mapas):
    """Concilia ou insere, registrando os vínculos na mesma transação."""
    totais = {grupo: {"inseridos": 0, "conciliados": 0} for grupo in TABELAS_MIGRADAS}
    for grupo in TABELAS_MIGRADAS:
        for registro in dados_transformados[grupo]:
            convertido = remapear_vinculos(grupo, registro, mapas)
            destino = controle.localizar(grupo, convertido)
            if destino is None:
                destino = controle.inserir(grupo, convertido)
                totais[grupo]["inseridos"] += 1
            else:
                totais[grupo]["conciliados"] += 1
            controle.registrar(grupo, registro["id"], destino)
            mapas[grupo][registro["id"]] = destino
    controle.verificar()
    return totais
