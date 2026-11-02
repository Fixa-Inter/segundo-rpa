from pathlib import Path

from psycopg2 import sql

from load.validacao import TABELAS_MIGRADAS
from transform.validacao import VINCULOS


CHAVES_NATURAIS = {
    "instituicoes": ("dominio_email",),
    "unidades": ("cnpj",),
    "super_administradores": ("email",),
    "usuarios": ("email",),
}


class CorrespondenciaAmbigua(ValueError):
    def __init__(self, grupo, id_origem, candidatos, motivo):
        self.detalhes = {"grupo": grupo, "id_origem": id_origem,
                         "ids_destino": list(candidatos), "motivo": motivo}
        super().__init__(f"Correspondência ambígua em {grupo}, ID de origem {id_origem}; revisão necessária.")


def remapear_vinculos(grupo, registro, mapas):
    convertido = dict(registro)
    for campo, pai in VINCULOS.get(grupo, {}).items():
        id_origem = registro[campo]
        if id_origem not in mapas[pai]:
            raise ValueError(f"{grupo}, ID {registro['id']}: vínculo {campo} sem correspondência.")
        convertido[campo] = mapas[pai][id_origem]
    return convertido


class Correspondencia:
    def __init__(self, conn, origem="legado"):
        self.conn = conn
        self.origem = origem

    def preparar(self):
        caminho = Path(__file__).resolve().parents[1] / "sql/rpa_correspondencia.sql"
        with self.conn.cursor() as cursor:
            cursor.execute(caminho.read_text(encoding="utf-8"))

    def carregar(self):
        mapas = {grupo: {} for grupo in TABELAS_MIGRADAS}
        por_tabela = {tabela: grupo for grupo, tabela in TABELAS_MIGRADAS.items()}
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT tabela, id_origem, id_destino FROM public.rpa_correspondencia WHERE origem = %s", (self.origem,))
            for tabela, origem, destino in cursor.fetchall():
                if tabela not in por_tabela:
                    raise ValueError("Correspondência com tabela desconhecida; revise o controle do RPA.")
                mapas[por_tabela[tabela]][origem] = destino
        return mapas

    def bloquear_tabelas(self):
        # Serializa a conferência e a inserção, inclusive com escritas do app.
        with self.conn.cursor() as cursor:
            cursor.execute("SET LOCAL lock_timeout = '5s'")
            tabelas = sql.SQL(", ").join(sql.Identifier("public", tabela) for tabela in TABELAS_MIGRADAS.values())
            cursor.execute(sql.SQL("LOCK TABLE {} IN SHARE ROW EXCLUSIVE MODE").format(tabelas))

    def verificar(self):
        # Não usa FK polimórfica: verifica a existência em cada tabela real.
        with self.conn.cursor() as cursor:
            for tabela in TABELAS_MIGRADAS.values():
                cursor.execute(sql.SQL(
                    "SELECT c.id_origem FROM public.rpa_correspondencia c "
                    "LEFT JOIN public.{} d ON d.id = c.id_destino "
                    "WHERE c.origem = %s AND c.tabela = %s AND d.id IS NULL LIMIT 1"
                ).format(sql.Identifier(tabela)), (self.origem, tabela))
                if cursor.fetchone() is not None:
                    raise ValueError(f"Correspondência inválida em {tabela}: registro de destino ausente.")

    def localizar(self, grupo, registro):
        campos = CHAVES_NATURAIS.get(grupo, tuple(c for c in registro if c != "id"))
        if not campos:
            raise ValueError(f"Nenhum campo de identificação disponível para {grupo}.")
        condicoes = sql.SQL(" AND ").join(
            (sql.SQL("LOWER(BTRIM({})) IS NOT DISTINCT FROM LOWER(BTRIM(%s))")
             if campo in ("email", "dominio_email") and grupo in CHAVES_NATURAIS
             else sql.SQL("{} IS NOT DISTINCT FROM %s")).format(sql.Identifier(campo))
            for campo in campos
        )
        with self.conn.cursor() as cursor:
            cursor.execute(sql.SQL("SELECT id FROM public.{} WHERE {} LIMIT 2").format(
                sql.Identifier(TABELAS_MIGRADAS[grupo]), condicoes
            ), tuple(registro[campo] for campo in campos))
            encontrados = cursor.fetchall()
        if len(encontrados) > 1:
            raise CorrespondenciaAmbigua(grupo, registro["id"], [r[0] for r in encontrados], "multiplas_correspondencias")
        if not encontrados:
            return None
        destino = encontrados[0][0]
        # Uma chave natural global não pode trocar o vínculo de unidade/instituição.
        for campo in VINCULOS.get(grupo, {}):
            with self.conn.cursor() as cursor:
                cursor.execute(sql.SQL("SELECT {} FROM public.{} WHERE id = %s").format(
                    sql.Identifier(campo), sql.Identifier(TABELAS_MIGRADAS[grupo])
                ), (destino,))
                if cursor.fetchone()[0] != registro[campo]:
                    raise CorrespondenciaAmbigua(grupo, registro["id"], [destino], "vinculo_divergente_" + campo)
        return destino

    def inserir(self, grupo, registro):
        campos = tuple(c for c in registro if c != "id")
        with self.conn.cursor() as cursor:
            cursor.execute(sql.SQL("INSERT INTO public.{} ({}) VALUES ({}) RETURNING id").format(
                sql.Identifier(TABELAS_MIGRADAS[grupo]),
                sql.SQL(", ").join(map(sql.Identifier, campos)),
                sql.SQL(", ").join(sql.Placeholder() for _ in campos),
            ), tuple(registro[campo] for campo in campos))
            return cursor.fetchone()[0]

    def registrar(self, grupo, id_origem, id_destino):
        with self.conn.cursor() as cursor:
            cursor.execute(
                "SELECT id_origem FROM public.rpa_correspondencia "
                "WHERE origem = %s AND tabela = %s AND id_destino = %s",
                (self.origem, TABELAS_MIGRADAS[grupo], id_destino),
            )
            anterior = cursor.fetchone()
            if anterior is not None and anterior[0] != id_origem:
                raise CorrespondenciaAmbigua(grupo, id_origem, [id_destino], "destino_ja_associado_a_outra_origem")
            cursor.execute(
                "INSERT INTO public.rpa_correspondencia (origem, tabela, id_origem, id_destino) VALUES (%s, %s, %s, %s)",
                (self.origem, TABELAS_MIGRADAS[grupo], id_origem, id_destino),
            )
