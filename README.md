# RPA – FIXA

Leva novos cadastros do legado para o banco normalizado a cada 20 minutos. Abrange instituição, plano, super admin, unidade, usuário, contrato, pagamento e foto de usuário.

## Como evitamos duplicação

O RPA mantém a tabela `rpa_correspondencia` no normalizado, ligando o ID do legado ao ID do destino. Os IDs não precisam ser iguais: novos cadastros recebem o ID gerado pelo próprio banco, e os vínculos são traduzidos antes de inserir os registros dependentes.

Antes de inserir, verifica se o registro já está mapeado ou se já existe no destino:

| Cadastro | Como reconhecer um registro existente |
|---|---|
| Usuário e super admin | E-mail, ignorando maiúsculas e espaços nas pontas. |
| Unidade | CNPJ. |
| Instituição | Domínio, ignorando maiúsculas e espaços nas pontas. |
| Plano, contrato, pagamento e foto | Todos os campos convertidos, exceto o ID, incluindo datas e vínculos já traduzidos. |

Se achar um único registro compatível, salva a correspondência e não o duplica. Se não achar, insere e registra o novo ID. Se achar mais de um candidato, um vínculo divergente ou dois registros do legado tentando usar o mesmo destino, interrompe a rodada e registra o caso no relatório para revisão. Não escolhe por nome ou ID igual.

Registros já mapeados, inclusive inativos, não são atualizados nem reativados. Alterações e exclusões posteriores no legado não são replicadas. Uma correspondência cujo destino foi apagado também interrompe a rodada; o RPA não recria o registro silenciosamente.

A correspondência é permanente: **não deve ser apagada entre rodadas nem junto dos relatórios**. O script `sql/rpa_correspondencia.sql` cria esse controle automaticamente na primeira execução; a conta do destino precisa poder criá-lo uma vez e depois consultar/inserir seus registros.

## Conferência e gravação

1. Obtém um bloqueio no PostgreSQL para impedir duas instâncias do RPA ao mesmo tempo.
2. Extrai os dados, lê as correspondências e valida os registros ainda não mapeados.
3. Traduz os vínculos e concilia ou insere na ordem das dependências.
4. Verifica se todos os IDs de destino do controle existem antes do commit.
5. Confirma os cadastros e as correspondências na mesma transação.

Se houver erro ou ambiguidade, as inserções da rodada são revertidas. Para a conferência não disputar com alterações do app, a etapa de conciliação bloqueia brevemente escritas nas tabelas envolvidas. Se não conseguir o bloqueio em cinco segundos, falha e tenta novamente na próxima rodada.

O RPA não inventa dados para preencher campos obrigatórios nem copia a senha da instituição para outra entidade. Verificações temporárias de cadastro e views do legado não são importadas.

## Relatórios como artifacts

Cada execução gera Markdown e JSON com resultado, duração, extraídos, já mapeados, candidatos, conciliados e inseridos confirmados por grupo. Casos ambíguos mostram grupo, ID do legado, até dois IDs candidatos e o motivo, sem nomes, e-mails, hashes ou linhas completas do banco.

Os arquivos ficam em **Actions → Sincronizar RPA → execução → Artifacts**. Não usamos outro repositório nem `REPORTS_TOKEN`; o Actions usa seu token automático.

Cada artifact tem retenção de **1 dia** (`retention-days: 1`) e expira após esse prazo, contado a partir do seu envio. O GitHub faz a limpeza; não usamos script de exclusão nem permissão `Actions: write`. Não é uma limpeza única de todos os relatórios em um horário fixo. [Retenção](https://github.com/actions/upload-artifact#retention-period).

Com uma rodada a cada 20 minutos, são cerca de 72 artifacts por dia, além de execuções manuais e novas tentativas. Como os arquivos contêm só contagens e metadados, o volume tende a ser pequeno. O prazo não afeta os dados migrados nem a tabela permanente de correspondência. A limitação é perder os detalhes de um incidente que só for investigado depois de 24 horas; baixe o relatório antes de expirar quando precisar guardar uma evidência.

A retenção do artifact não define a dos logs e do histórico do workflow, que seguem a configuração do repositório. O consumo das execuções, incluindo os testes e o PostgreSQL temporário a cada 20 minutos, também é separado do armazenamento dos relatórios.

Mesmo sem novidades ou com falha, o workflow tenta finalizar e anexar o relatório. Se o commit não puder ser confirmado, as inserções aparecem como não confirmadas. Falhas que impeçam o job de iniciar ou cancelamentos abruptos podem impedir a geração ou o envio.

## Configuração e execução

- Origem: `LEGADO_HOST`, `LEGADO_PORT`, `LEGADO_NAME`, `LEGADO_USER` e `LEGADO_PASS`.
- Destino: `NORM_HOST`, `NORM_PORT`, `NORM_NAME`, `NORM_USER` e `NORM_PASS`.
- Localmente, use o ambiente ou `.env`, ignorado pelo Git. No GitHub, cadastre os dez nomes em **Settings → Secrets and variables → Actions**.
- O normalizado precisa ter o esquema atual criado; pode ter dados, que serão conciliados pelas regras acima.
- Publique `.github/workflows/rpa.yaml` na branch padrão para agendar; também é possível rodar em **Actions → Sincronizar RPA → Run workflow**. O agendamento pode sofrer atrasos.

```powershell
python -m pip install -r requirements.txt
python main.py
```

Localmente, os relatórios ficam em `.rpa_reports/`, fora do versionamento.

## Testes

```powershell
python -B -m unittest discover -s tests -v
```

Os testes unitários usam dados fictícios. No Actions, os testes de integração usam um PostgreSQL temporário chamado `rpa_test`, antes de acessar os bancos configurados nos secrets. Eles conferem IDs diferentes, tradução dos vínculos, conciliação de registros existentes, repetição sem duplicação e rollback por ambiguidade.

Localmente, os testes de integração só executam com `RPA_TEST_DSN` apontando para `localhost` ou `127.0.0.1`, no banco `rpa_test`. Eles recriam as tabelas desse banco de teste e não usam `NORM_*`.
