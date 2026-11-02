import argparse
import os

from relatorio import Relatorio, finalizar_workflow


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("acao", choices=("iniciar", "finalizar"))
    args = parser.parse_args()
    arquivo = os.getenv("RPA_REPORT_FILE", ".rpa_reports/workflow/relatorio.json")
    if args.acao == "iniciar":
        Relatorio(arquivo).etapa("workflow_preparacao")
    else:
        finalizar_workflow(arquivo, os.getenv("RPA_WORKFLOW_RESULT", "failure"))


if __name__ == "__main__":
    main()
