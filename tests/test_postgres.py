from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlparse

import psycopg2
from psycopg2 import sql

from main import main
from load.correspondencia import Correspondencia, CorrespondenciaAmbigua, remapear_vinculos
from load.validacao import TABELAS_MIGRADAS
from transform._transform_all import transform_all
from test_migracao import origem


@unittest.skipUnless(os.getenv("RPA_TEST_DSN"), "PostgreSQL temporário não configurado; o Actions fornece RPA_TEST_DSN")
class PostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn = os.environ["RPA_TEST_DSN"]
        parsed = urlparse(cls.dsn)
        if parsed.hostname not in ("localhost", "127.0.0.1") or parsed.path != "/rpa_test":
            raise RuntimeError("Os testes só aceitam PostgreSQL local com banco rpa_test.")
        with psycopg2.connect(cls.dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                if cursor.fetchone()[0] != "rpa_test":
                    raise RuntimeError("Banco de testes inválido.")
                for tabela in ("rpa_correspondencia", *reversed(tuple(TABELAS_MIGRADAS.values()))):
                    cursor.execute(sql.SQL("DROP TABLE IF EXISTS public.{} CASCADE").format(sql.Identifier(tabela)))
                cursor.execute((Path(__file__).parent / "fixtures/destino.sql").read_text(encoding="utf-8"))
            Correspondencia(conn).preparar()

    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.arquivo = Path(pasta.name) / "teste.json"
        env = patch.dict(os.environ, {"RPA_REPORT_FILE": str(self.arquivo)})
        env.start()
        self.addCleanup(env.stop)
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cursor:
                tabelas = ["rpa_correspondencia", *TABELAS_MIGRADAS.values()]
                cursor.execute(sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
                    sql.SQL(", ").join(sql.Identifier("public", t) for t in tabelas)))

    def rodar(self, dados=None):
        with patch("main.conectar_destino", side_effect=lambda: psycopg2.connect(self.dsn)), patch(
            "main.extract_all", return_value=dados or origem()
        ):
            return main()

    def consulta(self, query, params=()):
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

    def semear(self, dados, inicio=100):
        convertidos = transform_all(dados)
        mapas = {g: {} for g in TABELAS_MIGRADAS}
        with psycopg2.connect(self.dsn) as conn:
            controle = Correspondencia(conn)
            for grupo, tabela in TABELAS_MIGRADAS.items():
                with conn.cursor() as cursor:
                    cursor.execute("SELECT setval(pg_get_serial_sequence(%s, 'id'), %s, false)", ("public." + tabela, inicio))
                for registro in convertidos[grupo]:
                    destino = controle.inserir(grupo, remapear_vinculos(grupo, registro, mapas))
                    mapas[grupo][registro["id"]] = destino
        return mapas

    def test_ids_diferentes_vinculos_corretos_e_reexecucao(self):
        dados_nativos = origem()
        dados_nativos["instituicoes"][0]["dominio_email"] = "nativo.example"
        dados_nativos["unidades"][0]["cnpj"] = "99123456000190"
        dados_nativos["usuarios"][0]["email"] = "nativo@teste.example"
        dados_nativos["super_administradores"][0]["email"] = "interno@teste.example"
        dados_nativos["planos"][0]["descricao"] = "plano criado no destino"
        self.semear(dados_nativos, inicio=100)
        resumo = self.rodar()
        self.assertEqual(sum(resumo.values()), 8)
        mapa = {t: (o, d) for t, o, d in self.consulta("SELECT tabela, id_origem, id_destino FROM rpa_correspondencia")}
        self.assertTrue(all(o != d for o, d in mapa.values()))
        usuario = mapa["usuario"][1]
        unidade = mapa["unidade"][1]
        self.assertEqual(self.consulta("SELECT unidade_id FROM usuario WHERE id = %s", (usuario,))[0][0], unidade)
        contrato = mapa["contrato"][1]
        self.assertEqual(self.consulta("SELECT unidade_id, plano_id FROM contrato WHERE id = %s", (contrato,))[0],
                         (unidade, mapa["plano"][1]))
        self.assertEqual(sum(self.rodar().values()), 0)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM rpa_correspondencia")[0][0], 8)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM usuario")[0][0], 2)

    def test_dados_ja_existentes_sao_conciliados_sem_duplicar(self):
        mapas = self.semear(origem())
        self.assertEqual(sum(self.rodar().values()), 0)
        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
        self.assertEqual(sum(v["conciliados"] for v in dados["tabelas"].values()), 8)
        self.assertEqual(self.consulta("SELECT id_destino FROM rpa_correspondencia WHERE tabela = 'usuario'")[0][0], mapas["usuarios"][5])
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM usuario")[0][0], 1)

    def test_usuario_novo_referencia_unidade_ja_mapeada(self):
        self.rodar()
        dados = origem()
        novo = deepcopy(dados["usuarios"][0])
        novo.update(id=99, email="novo@teste.example")
        dados["usuarios"].append(novo)
        resumo = self.rodar(dados)
        self.assertEqual(sum(resumo.values()), 1)
        self.assertEqual(resumo["usuarios"], 1)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM usuario")[0][0], 2)

    def test_ambiguidade_cancela_todos_os_inserts_e_gera_relatorio(self):
        plano = transform_all(origem())["planos"][0]
        with psycopg2.connect(self.dsn) as conn:
            controle = Correspondencia(conn)
            controle.inserir("planos", plano)
            controle.inserir("planos", plano)
        with self.assertRaises(CorrespondenciaAmbigua):
            self.rodar()
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM rpa_correspondencia")[0][0], 0)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM instituicao")[0][0], 0)
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM plano")[0][0], 2)
        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
        self.assertEqual(dados["ambiguidades"][0]["grupo"], "planos")
        self.assertTrue(all(v["inseridos_confirmados"] == 0 for v in dados["tabelas"].values()))

    def test_destino_removido_nao_recria_registro_mapeado(self):
        self.rodar()
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM foto")
        with self.assertRaisesRegex(ValueError, "registro de destino ausente"):
            self.rodar()
        self.assertEqual(self.consulta("SELECT COUNT(*) FROM foto")[0][0], 0)

    def test_chave_natural_com_vinculo_diferente_exige_revisao(self):
        mapas = self.semear(origem())
        usuario = mapas["usuarios"][5]
        unidade = mapas["unidades"][2]
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO unidade (instituicao_id,nome,cnpj,logradouro,numero,bairro,cidade,estado,cep) "
                               "SELECT instituicao_id,'Outra unidade','88123456000190',logradouro,numero,bairro,cidade,estado,cep "
                               "FROM unidade WHERE id=%s RETURNING id", (unidade,))
                outra = cursor.fetchone()[0]
                cursor.execute("UPDATE usuario SET unidade_id=%s WHERE id=%s", (outra, usuario))
        with self.assertRaises(CorrespondenciaAmbigua):
            self.rodar()
        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
        self.assertEqual(dados["ambiguidades"][0]["motivo"], "vinculo_divergente_unidade_id")
        self.assertEqual(self.consulta("SELECT unidade_id FROM usuario WHERE id=%s", (usuario,))[0][0], outra)


if __name__ == "__main__":
    unittest.main()
