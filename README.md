<div align="center">

# FIXA · RPA de Migração

Sincronização transacional de cadastros do sistema legado com o banco normalizado.

![badge](https://img.shields.io/badge/Python-Automation-3776AB?logo=python&logoColor=white) ![badge](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white) ![badge](https://img.shields.io/badge/GitHub_Actions-Scheduled-2088FF?logo=githubactions&logoColor=white) ![badge](https://img.shields.io/badge/License-MIT-green)

</div>

---

## ✨ Visão geral

O RPA processa novos cadastros sem assumir que os identificadores do legado e do destino são iguais. As correspondências são persistidas e os vínculos traduzidos antes da gravação.

## 🚀 Funcionalidades

- Migração de instituições, planos e superadministradores
- Migração de unidades, usuários, contratos e pagamentos
- Migração de fotos de usuários
- Tradução de identificadores entre origem e destino
- Conciliação com registros existentes e prevenção de duplicidades
- Detecção de conflitos e registros ambíguos
- Execução transacional com rollback
- Bloqueio de execuções simultâneas
- Correspondência permanente entre IDs
- Relatórios em Markdown e JSON
- Execução agendada a cada 20 minutos
- Testes unitários e de integração

## 🧰 Tecnologias

| Área | Tecnologias |
| --- | --- |
| **Linguagem** | Python |
| **Banco de dados** | PostgreSQL |
| **Acesso a dados** | psycopg2 |
| **Automação** | GitHub Actions |
| **Testes** | Unittest |

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE).

---

<div align="center">
  Desenvolvido pela <strong>Fixa-Inter</strong>.
</div>
