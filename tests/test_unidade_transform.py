from datetime import datetime
import unittest

from transform.unidade_transform import transform_unidades


class UnidadeTransformTest(unittest.TestCase):
    def unidade(self, **alteracoes):
        unidade = {
            "id": 7,
            "fk_instituicao_id": 2,
            "nome": "Unidade Centro",
            "cnpj": "00123456000190",
            "rua": "Rua Central",
            "numero": "10A",
            "complemento": None,
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
            "cep": "01234567",
            "data_criacao": datetime(2026, 10, 26, 9, 30),
        }
        unidade.update(alteracoes)
        return unidade

    def transformar(self, **alteracoes):
        return transform_unidades([self.unidade(**alteracoes)])[0]

    def test_preserva_zeros_e_timestamp(self):
        origem = self.unidade()
        destino = transform_unidades([origem])[0]
        self.assertEqual(destino["cnpj"], "00123456000190")
        self.assertEqual(destino["cep"], "01234567")
        self.assertEqual(destino["data_criacao"], origem["data_criacao"])
        self.assertIsNone(destino["complemento"])

    def test_remove_apenas_padding_dos_antigos_char(self):
        destino = self.transformar(cnpj="123  ", estado="S ", cep="0123    ")
        self.assertEqual(destino["cnpj"], "123")
        self.assertEqual(destino["estado"], "S")
        self.assertEqual(destino["cep"], "0123")
        self.assertEqual(self.transformar(rua="Rua  ")["logradouro"], "Rua  ")

    def test_varchar_aceita_comprimento_menor_sem_completar(self):
        self.assertEqual(self.transformar(cep="0123")["cep"], "0123")

    def test_rejeita_texto_longo_sem_truncar(self):
        for campo, limite in [("cnpj", 14), ("estado", 2), ("cep", 8),
                              ("nome", 100), ("numero", 10), ("rua", 100),
                              ("complemento", 100)]:
            with self.subTest(campo=campo):
                with self.assertRaisesRegex(ValueError, "VARCHAR"):
                    self.transformar(**{campo: "X" * (limite + 1)})

    def test_rejeita_identificadores_numericos_ou_nulos(self):
        for campo in ["cnpj", "estado", "cep"]:
            for valor in [None, 123, 1.5, True]:
                with self.subTest(campo=campo, valor=valor):
                    with self.assertRaisesRegex(ValueError, campo):
                        self.transformar(**{campo: valor})

    def test_nome_vazio_usa_identificacao_existente(self):
        self.assertEqual(self.transformar(nome="")["nome"], "Unidade 7")


if __name__ == "__main__":
    unittest.main()
