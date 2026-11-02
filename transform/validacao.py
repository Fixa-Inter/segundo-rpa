from datetime import date, datetime
from decimal import Decimal, InvalidOperation


# Campos que o RPA envia e que são NOT NULL no destino.
OBRIGATORIOS = {
    "instituicoes": "id nome tipo_instituicao dominio_email data_criacao",
    "unidades": "id instituicao_id nome cnpj logradouro numero bairro cidade estado cep data_criacao",
    "planos": "id nome valor duracao_meses data_criacao",
    "super_administradores": "id nome email senha_hash",
    "usuarios": "id unidade_id nome_completo email tipo_acesso senha_hash cargo data_nascimento data_criacao esta_ativo primeiro_acesso",
    "contratos": "id plano_id unidade_id data_inicio data_fim status data_criacao",
    "pagamentos": "id contrato_id data_pagamento valor_pago status metodo_pagamento data_criacao",
    "fotos_usuario": "id usuario_id url data_criacao",
}

ORIGEM = {
    "instituicoes": {"data_criacao": "data_cadastro"},
    "unidades": {"instituicao_id": "fk_instituicao_id", "logradouro": "rua"},
    "planos": {"valor": "valor_mensal"},
    "usuarios": {"unidade_id": "fk_endereco_id", "nome_completo": "nome"},
    "contratos": {"plano_id": "fk_plano_id", "unidade_id": "fk_endereco_id", "data_fim": "data_vencimento"},
    "pagamentos": {"contrato_id": "fk_contrato_id", "valor_pago": "valor", "status": "foi_realizado"},
    "fotos_usuario": {"usuario_id": "fk_usuario_id", "data_criacao": "data_registro"},
}

TEXTOS = {
    "instituicoes": {"nome": 100, "email_corporativo": 100, "dominio_email": 100},
    "unidades": {"nome": 100, "cnpj": 14, "logradouro": 100, "numero": 10, "complemento": 100, "bairro": 100, "cidade": 100, "estado": 2, "cep": 8},
    "planos": {"nome": 100, "descricao": 255},
    "super_administradores": {"nome": 100, "email": 100, "senha_hash": 255},
    "usuarios": {"nome_completo": 100, "email": 100, "senha_hash": 255, "cargo": 100},
    "fotos_usuario": {"url": 255},
}

VINCULOS = {
    "unidades": {"instituicao_id": "instituicoes"},
    "usuarios": {"unidade_id": "unidades"},
    "contratos": {"plano_id": "planos", "unidade_id": "unidades"},
    "pagamentos": {"contrato_id": "contratos"},
    "fotos_usuario": {"usuario_id": "usuarios"},
}

UNICOS = {
    "instituicoes": ("email_corporativo", "dominio_email"),
    "unidades": ("cnpj",),
    "usuarios": ("email",),
    "super_administradores": ("email",),
}


def _erro(grupo, registro, campo, motivo):
    # Não inclui valores pessoais, credenciais ou URLs nos erros.
    return f"{grupo}, ID {registro.get('id', '?')}, campo {campo}: {motivo}"


def _falhar(erros):
    if erros:
        raise ValueError("Dados incompatíveis com o destino:\n" + "\n".join(erros))


def validar_origem(dados):
    """Impede comparações com NULL e identifica campos faltantes antes de transformar."""
    erros = []
    for grupo, campos in OBRIGATORIOS.items():
        for registro in dados[grupo]:
            for campo in campos.split():
                if grupo == "unidades" and campo == "nome":
                    continue  # Preserva o fallback por ID já existente.
                origem = ORIGEM.get(grupo, {}).get(campo, campo)
                if registro.get(origem) is None:
                    erros.append(_erro(grupo, registro, origem, "obrigatório no destino"))
    _falhar(erros)


def validar_destino(dados, ids_existentes=None):
    """Valida os lotes completos antes de qualquer INSERT."""
    erros = []
    ids = {}
    for grupo, campos in OBRIGATORIOS.items():
        ids[grupo] = set()
        vistos = {campo: set() for campo in UNICOS.get(grupo, ())}
        for registro in dados[grupo]:
            for campo in campos.split():
                if registro.get(campo) is None:
                    erros.append(_erro(grupo, registro, campo, "obrigatório no destino"))
            identificador = registro.get("id")
            if type(identificador) is not int:
                erros.append(_erro(grupo, registro, "id", "esperado inteiro"))
            elif identificador in ids[grupo]:
                erros.append(_erro(grupo, registro, "id", "duplicado no lote"))
            else:
                ids[grupo].add(identificador)
            for campo, limite in TEXTOS.get(grupo, {}).items():
                valor = registro.get(campo)
                if valor is not None and (not isinstance(valor, str) or len(valor) > limite):
                    erros.append(_erro(grupo, registro, campo, f"esperado texto de até {limite} caracteres"))
            for campo, valores in vistos.items():
                valor = registro.get(campo)
                if valor is not None:
                    if valor in valores:
                        erros.append(_erro(grupo, registro, campo, "valor duplicado no lote"))
                    valores.add(valor)
            for campo in ("esta_ativo", "primeiro_acesso"):
                if campo in registro and type(registro[campo]) is not bool:
                    erros.append(_erro(grupo, registro, campo, "esperado booleano"))
            for campo in ("data_criacao", "data_pagamento", "data_inicio", "data_fim", "data_nascimento"):
                valor = registro.get(campo)
                if valor is not None and not isinstance(valor, (date, datetime)):
                    erros.append(_erro(grupo, registro, campo, "esperada data ou timestamp"))
            for campo in ("valor", "valor_pago"):
                if campo in registro:
                    try:
                        valor = Decimal(str(registro[campo]))
                        valido = valor.is_finite() and 0 <= valor <= Decimal("99999999.99")
                    except (InvalidOperation, ValueError):
                        valido = False
                    if not valido:
                        erros.append(_erro(grupo, registro, campo, "valor incompatível com DECIMAL(10,2)"))
    referencias = {grupo: valores | set((ids_existentes or {}).get(grupo, ()))
                   for grupo, valores in ids.items()}
    for grupo, vinculos in VINCULOS.items():
        for registro in dados[grupo]:
            for campo, pai in vinculos.items():
                if registro.get(campo) not in referencias[pai]:
                    erros.append(_erro(grupo, registro, campo, f"referência ausente no lote e no destino de {pai}"))
    _falhar(erros)
