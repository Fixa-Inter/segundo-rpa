import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from main import main
from relatorio import Relatorio, finalizar_workflow
from load.validacao import TABELAS_MIGRADAS
from test_migracao import origem


class RelatoriosTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.arquivo = Path(pasta.name) / "123-1.json"
        self.env = {"RPA_REPORT_FILE": str(self.arquivo),
 "GITHUB_REPOSITORY": "Fixa-Inter/rpa",
                    "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1"}
        patcher = patch.dict(os.environ, self.env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def ler(self):
        return json.loads(self.arquivo.read_text(encoding="utf-8"))

    def rodar(self, dados=None, falha=None, commit_falha=False):
        with patch("main.extract_all", return_value=dados or origem()), patch("main.Correspondencia") as controle_cls, patch(
            "main.load_all", side_effect=falha,
            return_value={g: {"inseridos": len((dados or origem())[g]), "conciliados": 0} for g in TABELAS_MIGRADAS}
        ), patch("main.conectar_destino") as connect:
            controle_cls.return_value.carregar.return_value = {g: {} for g in TABELAS_MIGRADAS}
            conn = connect.return_value
            conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (True,)
            if commit_falha:
                conn.__exit__.side_effect = RuntimeError("falha de commit com dado privado")
            return main()

    def test_sucesso_registra_apenas_contagens_e_commit(self):
        self.rodar()
        dados = self.ler()
        self.assertEqual(dados["status"], "sucesso")
        self.assertEqual(dados["transacao"], "confirmada")
        self.assertEqual(dados["tabelas"]["usuarios"]["inseridos_confirmados"], 1)
        texto = self.arquivo.with_suffix(".md").read_text(encoding="utf-8")
        for proibido in ("hash-ficticio", "pessoa@teste.example", "token-ficticio", "Rua teste"):
            self.assertNotIn(proibido, texto + self.arquivo.read_text(encoding="utf-8"))
        self.assertIn("# Relatório do RPA", texto)
        self.assertIsNotNone(dados["duracao_segundos"])

    def test_sem_novidades_tem_relatorio(self):
        self.rodar({grupo: [] for grupo in TABELAS_MIGRADAS})
        self.assertEqual(self.ler()["status"], "sem_novidades")

    def test_falha_na_carga_nao_declara_insercoes_confirmadas(self):
        with self.assertRaises(RuntimeError):
            self.rodar(falha=RuntimeError("senha-privada"))
        dados = self.ler()
        self.assertEqual(dados["status"], "falha")
        self.assertEqual(dados["etapa"], "conciliando_carregando")
        self.assertEqual(dados["tabelas"]["usuarios"]["candidatos"], 1)
        self.assertEqual(dados["tabelas"]["usuarios"]["inseridos_confirmados"], 0)
        self.assertNotIn("senha-privada", self.arquivo.read_text(encoding="utf-8"))

    def test_commit_incerto_nao_e_reportado_como_rollback_confirmado(self):
        with self.assertRaises(RuntimeError):
            self.rodar(commit_falha=True)
        dados = self.ler()
        self.assertEqual(dados["transacao"], "resultado_nao_confirmado")
        self.assertIsNone(dados["tabelas"]["usuarios"]["inseridos_confirmados"])

    def test_rodada_ignorada_tambem_tem_relatorio(self):
        with patch("main.conectar_destino") as connect:
            connect.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (False,)
            main()
        self.assertEqual(self.ler()["status"], "ignorada")

    def test_ambiguidades_aparecem_no_json_e_markdown(self):
        from load.correspondencia import CorrespondenciaAmbigua
        with self.assertRaises(CorrespondenciaAmbigua):
            self.rodar(falha=CorrespondenciaAmbigua("usuarios", 5, [20, 21], "multiplas_correspondencias"))
        dados = self.ler()
        self.assertEqual(dados["erro"]["categoria"], "ambiguidade")
        self.assertEqual(dados["ambiguidades"][0]["ids_destino"], [20, 21])
        texto = self.arquivo.with_suffix(".md").read_text(encoding="utf-8")
        self.assertIn("## Casos ambíguos", texto)

    def test_workflow_que_falha_antes_do_rpa_tem_relatorio(self):
        relatorio = Relatorio()
        relatorio.etapa("workflow_preparacao")
        finalizar_workflow(self.arquivo, "failure")
        self.assertEqual(self.ler()["status"], "nao_executado")

    def test_cancelamento_preserva_incerteza_e_nao_sobrescreve_resultado_terminal(self):
        relatorio = Relatorio()
        relatorio.etapa("carregando")
        finalizar_workflow(self.arquivo, "cancelled")
        dados = self.ler()
        self.assertEqual(dados["status"], "cancelada")
        self.assertIsNone(dados["tabelas"]["usuarios"]["inseridos_confirmados"])
        finalizar_workflow(self.arquivo, "failure")
        self.assertEqual(self.ler()["status"], "cancelada")


if __name__ == "__main__":
    unittest.main()
