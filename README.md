# erp-para-contabil

Lê lançamentos do ERP, valida e gera o arquivo no layout que o sistema contábil importa.
**Sem IA no caminho crítico — de propósito.**

> Reimplementação pública de uma integração que mantenho em produção. Dados, schema e regras aqui são sintéticos.

## O problema

Toda competência, alguém monta a capa do fechamento numa planilha e redigita lançamento por lançamento no sistema contábil. Dois sistemas caros e uma pessoa cara no meio fazendo papel de cabo de rede.

## Rodando

```bash
python3 main.py                                                    # dataset com erros propositais
python3 main.py dados/lancamentos_corrigido.csv dados/de_para_completo.csv   # caminho feliz
```

Só stdlib. Sem instalar nada.

```
VALIDAÇÃO FALHOU — 3 problema(s), nada foi gerado:

  · lote 2026-08-02: partida dobrada não fecha — débito 27100.00 x crédito 27000.00 (dif. 100.00)
  · doc AD-9001 seq 1: sem de-para para 'ADIANTAMENTO EVENTO PATROCINIO FEIRA' (D) — processo para, não vai para conta de ajuste
```

## Decisões

**IA não entra aqui.** Lançamento ou bate, ou não bate: o requisito é exatidão, não plausibilidade. LLM introduz variância onde variância é o defeito, e o erro custa retrabalho fiscal com prazo legal. Se o problema crescesse, IA entraria só para classificar histórico livre sem de-para — e como sugestão em fila de aprovação, nunca escrevendo no arquivo.

**Arquivo, não API.** No mercado brasileiro a API do contábil ou não existe, ou é módulo à parte, ou muda na atualização do fornecedor. O importador de arquivo já existe e o fornecedor não pode quebrar sem quebrar o próprio produto.

**Validar antes de gerar.** Partida dobrada por lote. Não fecha, não gera, e aponta a linha. Arquivo inválido descoberto na importação custa duas vezes, já sob prazo.

**Idempotência por chave de origem** — `(lote, sistema, documento, seq)`. Rodar o mesmo período duas vezes não duplica. É o que faz a pessoa confiar o suficiente para rodar de novo na dúvida; automação em que ninguém confia volta a ser feita na mão.

**De-para em tabela com vigência por data.** Quem mantém plano de contas é a contabilidade, não o dev. Ela altera sem abrir chamado, e como era em maio segue reproduzível.

**Falha alto.** Conta não encontrada para o processo. Não cai em conta de ajuste — é onde erro mora em silêncio até alguém conciliar seis meses depois.

## Resultado

Na versão em produção: **~17h30/mês de digitação eliminadas**, apurado em KPI. Efeito não previsto: o fechamento parou de variar de critério entre meses.

## Stack

Python (stdlib) · CSV · `Decimal` para dinheiro, nunca `float`

MIT
