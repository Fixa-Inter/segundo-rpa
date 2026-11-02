from datetime import datetime, timezone
import json
import os
from pathlib import Path
import uuid


GRUPOS = ("instituicoes", "unidades", "planos", "super_administradores",
          "usuarios", "contratos", "pagamentos", "fotos_usuario")
TERMINAIS = {"sucesso", "sem_novidades", "ignorada", "falha", "nao_executado", "cancelada"}


def agora():
    return datetime.now(timezone.utc).isoformat()


class Relatorio:
    def __init__(self, arquivo=None):
        identificador = os.getenv("GITHUB_RUN_ID", uuid.uuid4().hex)
        tentativa = os.getenv("GITHUB_RUN_ATTEMPT", "1")
        self.arquivo = Path(arquivo or os.getenv(
            "RPA_REPORT_FILE", f".rpa_reports/relatorio-rpa-{identificador}-{tentativa}/relatorio.json"))
        repo = os.getenv("GITHUB_REPOSITORY", "local")
        self.dados = {
            "versao": 2, "id": f"{identificador}-{tentativa}", "repositorio_origem": repo,
            "inicio_utc": agora(), "fim_utc": None, "duracao_segundos": None,
            "status": "iniciada", "etapa": "preparacao", "transacao": "nao_iniciada",
            "workflow_url": (f"https://github.com/{repo}/actions/runs/{identificador}"
                             if os.getenv("GITHUB_RUN_ID") else None),
            "erro": None, "ambiguidades": [],
            "criterio_identificacao": "Correspondência persistida entre origem e destino, com conciliação por chaves e tradução de vínculos",
            "tabelas": {grupo: {"extraidos": None, "ja_mapeados": None,
                               "candidatos": None, "conciliados": 0, "inseridos_confirmados": 0}
                        for grupo in GRUPOS},
        }

    def etapa(self, nome):
        self.dados["etapa"] = nome
        self.salvar()

    def finalizar(self, status):
        self.dados["status"] = status
        self.dados["fim_utc"] = agora()
        self.dados["duracao_segundos"] = round((
            datetime.fromisoformat(self.dados["fim_utc"])
            - datetime.fromisoformat(self.dados["inicio_utc"])
        ).total_seconds(), 3)
        self.salvar()

    def salvar(self):
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo.write_text(json.dumps(self.dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.arquivo.with_suffix(".md").write_text(markdown(self.dados), encoding="utf-8")


def markdown(dados):
    linhas = ["# Relatório do RPA", "", f"- Execução: `{dados['id']}`",
              f"- Resultado: **{dados['status']}**", f"- Etapa: {dados['etapa']}",
              f"- Início (UTC): {dados['inicio_utc']}", f"- Fim (UTC): {dados['fim_utc']}",
              f"- Duração: {dados['duracao_segundos']} s", f"- Transação: {dados['transacao']}"]
    if dados.get("workflow_url"):
        linhas.append(f"- Workflow: {dados['workflow_url']}")
    linhas += ["", "| Grupo | Extraídos | Já mapeados | Candidatos | Conciliados | Inseridos confirmados |",
               "|---|---:|---:|---:|---:|---:|"]
    for grupo, valores in dados["tabelas"].items():
        contagens = [str(valores[c]) if valores[c] is not None else "não confirmado"
                     for c in ("extraidos", "ja_mapeados", "candidatos", "conciliados", "inseridos_confirmados")]
        linhas.append("| " + grupo + " | " + " | ".join(contagens) + " |")
    if dados.get("erro"):
        erro = dados["erro"]
        linhas += ["", f"Erro: {erro['categoria']}; SQLSTATE: {erro.get('sqlstate') or 'não disponível'}."]
    if dados.get("ambiguidades"):
        linhas += ["", "## Casos ambíguos", "",
                   "| Grupo | ID no legado | IDs candidatos no destino (até 2) | Motivo |",
                   "|---|---:|---|---|"]
        for caso in dados["ambiguidades"]:
            linhas.append(f"| {caso['grupo']} | {caso['id_origem']} | {', '.join(map(str, caso['ids_destino']))} | {caso['motivo']} |")
        linhas += ["", "A rodada foi interrompida para revisão, sem escolher um candidato automaticamente."]
    linhas += ["", "Critério atual: " + dados["criterio_identificacao"] + ".",
               "Contém apenas metadados e contagens, sem linhas do banco, dados pessoais ou credenciais.", ""]
    return "\n".join(linhas)


def finalizar_workflow(arquivo, resultado):
    relatorio = Relatorio(arquivo)
    if relatorio.arquivo.exists():
        relatorio.dados = json.loads(relatorio.arquivo.read_text(encoding="utf-8"))
    if relatorio.dados["status"] not in TERMINAIS:
        rodou = relatorio.dados["etapa"] not in ("preparacao", "workflow_preparacao")
        if rodou:
            for valores in relatorio.dados["tabelas"].values():
                valores["inseridos_confirmados"] = None
            relatorio.dados["transacao"] = "resultado_nao_confirmado"
        relatorio.dados["erro"] = {"categoria": "workflow_" + resultado, "sqlstate": None}
        relatorio.finalizar("cancelada" if resultado == "cancelled" else "falha" if rodou else "nao_executado")
    else:
        relatorio.salvar()
