from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg2

from db import conectar_origem, conectar_destino
from extract.usuario_extract import extract_usuarios
from extract.contrato_extract import extract_contratos
from transform._transform_all import transform_all
from load.validacao import selecionar_novos, TABELAS_MIGRADAS
from load.correspondencia import remapear_vinculos, Correspondencia, CorrespondenciaAmbigua
from main import main


def origem():
    data = datetime(2026, 1, 1, 12)
    return {
        "instituicoes": [{"id": 1, "nome": "Instituição teste", "tipo_instituicao": 1,
                          "email_corporativo": None, "dominio_email": "teste.example", "data_cadastro": data.date()}],
        "unidades": [{"id": 2, "fk_instituicao_id": 1, "nome": "Unidade teste",
                      "cnpj": "00123456000190", "rua": "Rua teste", "numero": "1A",
                      "complemento": None, "bairro": "Centro", "cidade": "São Paulo",
                      "estado": "SP", "cep": "01234567", "data_criacao": data}],
        "planos": [{"id": 3, "nome": "Plano teste", "valor_mensal": Decimal("10.50"),
                    "descricao": None, "duracao_meses": 12, "data_criacao": data}],
        "super_administradores": [{"id": 4, "nome": "Equipe teste", "email": "equipe@teste.example", "senha_hash": "hash-ficticio"}],
        "usuarios": [{"id": 5, "fk_endereco_id": 2, "nome": "Pessoa teste",
                      "email": "pessoa@teste.example", "tipo_acesso": 3, "senha_hash": "hash-ficticio",
                      "cargo": "Técnico", "data_nascimento": date(2000, 1, 1),
                      "data_criacao": data, "esta_ativo": False, "primeiro_acesso": True}],
        "contratos": [{"id": 6, "fk_plano_id": 3, "fk_endereco_id": 2,
                       "data_inicio": date(2026, 1, 1), "data_vencimento": date(2027, 1, 1),
                       "status": 1, "data_criacao": data}],
        "pagamentos": [{"id": 7, "fk_contrato_id": 6, "valor": Decimal("10.50"),
                        "foi_realizado": True, "metodo_pagamento": 3,
                        "data_pagamento": data, "data_criacao": data}],
        "fotos_usuario": [{"id": 8, "fk_usuario_id": 5, "url": "https://teste.example/foto", "data_registro": data}],
    }


class MigracaoTest(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        patcher = patch.dict("os.environ", {"RPA_REPORT_FILE": str(Path(pasta.name) / "teste.json")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_transformacao_completa_preserva_vinculos_hash_e_soft_delete(self):
        dados = transform_all(origem())
        self.assertEqual(dados["usuarios"][0]["tipo_acesso"], 3)
        self.assertEqual(dados["usuarios"][0]["senha_hash"], "hash-ficticio")
        self.assertFalse(dados["usuarios"][0]["esta_ativo"])
        self.assertEqual(dados["contratos"][0]["unidade_id"], 2)
        self.assertEqual(dados["fotos_usuario"][0]["usuario_id"], 5)
        self.assertEqual(dados["pagamentos"][0]["status"], 2)

    def test_pagamento_nao_realizado_vira_pendente(self):
        dados = origem()
        dados["pagamentos"][0]["foi_realizado"] = False
        self.assertEqual(transform_all(dados)["pagamentos"][0]["status"], 1)

    def test_nulos_obrigatorios_identificam_registro_e_campo(self):
        casos = [("instituicoes", "dominio_email"), ("usuarios", "cargo"),
                 ("usuarios", "data_nascimento"), ("usuarios", "esta_ativo"),
                 ("contratos", "data_vencimento"), ("pagamentos", "valor"),
                 ("fotos_usuario", "fk_usuario_id"), ("fotos_usuario", "url")]
        for grupo, campo in casos:
            with self.subTest(grupo=grupo, campo=campo):
                dados = origem()
                dados[grupo][0][campo] = None
                with self.assertRaisesRegex(ValueError, campo):
                    transform_all(dados)

    def test_rejeita_referencia_inexistente_antes_da_carga(self):
        dados = origem()
        dados["usuarios"][0]["fk_endereco_id"] = 99
        with self.assertRaisesRegex(ValueError, "referência ausente"):
            transform_all(dados)

    def test_rejeita_email_duplicado_sem_expor_o_valor(self):
        dados = origem()
        outro = deepcopy(dados["usuarios"][0])
        outro["id"] = 9
        dados["usuarios"].append(outro)
        with self.assertRaisesRegex(ValueError, "email: valor duplicado") as erro:
            transform_all(dados)
        self.assertNotIn(outro["email"], str(erro.exception))

    def test_rejeita_texto_longo_sem_truncar(self):
        dados = origem()
        dados["usuarios"][0]["cargo"] = "X" * 101
        with self.assertRaisesRegex(ValueError, "cargo"):
            transform_all(dados)

    def test_rejeita_data_fim_anterior_ao_inicio(self):
        dados = origem()
        dados["contratos"][0]["data_vencimento"] = date(2025, 1, 1)
        with self.assertRaisesRegex(ValueError, "Datas inválidas"):
            transform_all(dados)

    def test_rejeita_valor_fora_da_precisao_do_destino(self):
        dados = origem()
        dados["planos"][0]["valor_mensal"] = Decimal("100000000")
        with self.assertRaisesRegex(ValueError, "DECIMAL"):
            transform_all(dados)

    @patch("db.psycopg2.connect")
    def test_conexoes_retornam_abertas(self, connect):
        for funcao in (conectar_origem, conectar_destino):
            conn = MagicMock()
            connect.return_value = conn
            self.assertIs(funcao(), conn)
            conn.close.assert_not_called()

    @patch("db.psycopg2.connect", side_effect=psycopg2.OperationalError("detalhe privado"))
    def test_erro_conexao_nao_expoe_detalhes(self, connect):
        for funcao in (conectar_origem, conectar_destino):
            with self.assertRaises(ConnectionError) as erro:
                funcao()
            self.assertNotIn("detalhe privado", str(erro.exception))

    def test_extract_consulta_colunas_do_legado(self):
        for modulo, funcao, trecho in (
            ("extract.usuario_extract", extract_usuarios, "tipo_acesso"),
            ("extract.contrato_extract", extract_contratos, "status_contrato AS status"),
        ):
            with self.subTest(modulo=modulo), patch(modulo + ".conectar_origem") as connect:
                conn = connect.return_value
                cursor = conn.cursor.return_value.__enter__.return_value
                cursor.description = [("id",)]
                cursor.fetchall.return_value = []
                self.assertEqual(funcao(), [])
                query = cursor.execute.call_args.args[0]
                self.assertIn(trecho, query)
                self.assertNotIn("tipo_de_acesso", query)
                self.assertNotIn("gerente_id", query)
                conn.close.assert_called_once()

    def test_mesmo_id_no_destino_nao_prova_correspondencia(self):
        dados = origem()
        mapas = {g: {} for g in TABELAS_MIGRADAS}
        novos = selecionar_novos(dados, mapas)
        self.assertEqual(novos["usuarios"][0]["id"], 5)

    def test_traduz_vinculo_sem_alterar_o_registro_da_origem(self):
        registro = {"id": 5, "unidade_id": 2, "email": "teste@example.com"}
        convertido = remapear_vinculos("usuarios", registro, {"unidades": {2: 90}})
        self.assertEqual(convertido["unidade_id"], 90)
        self.assertEqual(registro["unidade_id"], 2)

    def test_vinculo_sem_mapeamento_nao_e_copiado_por_id(self):
        with self.assertRaisesRegex(ValueError, "sem correspondência"):
            remapear_vinculos("usuarios", {"id": 5, "unidade_id": 2}, {"unidades": {}})

    def test_insercao_deixa_o_banco_gerar_id(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (120,)
        destino = Correspondencia(conn).inserir("planos", {"id": 99, "nome": "Plano", "valor": 10})
        self.assertEqual(destino, 120)
        self.assertEqual(cursor.execute.call_args.args[1], ("Plano", 10))
        self.assertIn("RETURNING id", str(cursor.execute.call_args.args[0]))

    def test_ambiguidades_sao_explicitadas_sem_dados_pessoais(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [(10,), (11,)]
        with self.assertRaises(CorrespondenciaAmbigua) as erro:
            Correspondencia(conn).localizar("usuarios", {"id": 5, "email": "privado@example.com"})
        self.assertEqual(erro.exception.detalhes["ids_destino"], [10, 11])
        self.assertNotIn("privado", str(erro.exception))

    def test_duas_origens_nao_podem_reutilizar_o_mesmo_destino(self):
        conn = MagicMock()
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (4,)
        with self.assertRaises(CorrespondenciaAmbigua):
            Correspondencia(conn).registrar("usuarios", 5, 100)
        cursor.execute.assert_called_once()

    @patch("main.conectar_destino")
    @patch("main.Correspondencia")
    @patch("main.extract_all")
    def test_primeira_carga_e_reexecucao_sem_duplicar(self, extrair, controle_cls, connect):
        extrair.return_value = origem()
        controle = controle_cls.return_value
        mapas = {g: {} for g in TABELAS_MIGRADAS}
        controle.carregar.return_value = mapas
        controle.localizar.return_value = None
        controle.inserir.side_effect = range(100, 108)
        connect.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (True,)
        resumo = main()
        self.assertEqual(sum(resumo.values()), 8)
        self.assertEqual(mapas["usuarios"][5], 104)
        usuario = next(c.args[1] for c in controle.inserir.call_args_list if c.args[0] == "usuarios")
        self.assertEqual(usuario["unidade_id"], 103)
        controle.inserir.reset_mock()
        controle.registrar.reset_mock()
        resumo = main()
        self.assertEqual(sum(resumo.values()), 0)
        controle.inserir.assert_not_called()
        controle.registrar.assert_not_called()

    @patch("main.conectar_destino")
    @patch("main.extract_all")
    def test_outra_sincronizacao_em_execucao_nao_insere(self, extrair, connect):
        conn = connect.return_value
        conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (False,)
        self.assertEqual(main(), {})
        extrair.assert_not_called()
        conn.close.assert_called_once()

    @patch("main.conectar_destino")
    @patch("main.Correspondencia")
    @patch("main.extract_all")
    def test_falha_interrompe_transacao_e_fecha_conexao(self, extrair, controle_cls, connect):
        extrair.return_value = origem()
        controle = controle_cls.return_value
        controle.carregar.return_value = {g: {} for g in TABELAS_MIGRADAS}
        controle.localizar.return_value = None
        controle.inserir.side_effect = RuntimeError("falha simulada")
        conn = connect.return_value
        conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (True,)
        with self.assertRaisesRegex(RuntimeError, "falha simulada"):
            main()
        self.assertIs(conn.__exit__.call_args.args[0], RuntimeError)
        conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
