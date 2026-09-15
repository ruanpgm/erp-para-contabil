"""Lê lançamentos do ERP, valida e gera o arquivo do sistema contábil.

Sem IA no caminho crítico: lançamento contábil ou bate, ou não bate.
Só stdlib — roda com `python3 main.py`.
"""
import csv, sys, hashlib
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

RAIZ = Path(__file__).parent
ENTRADA = RAIZ / "dados" / "lancamentos.csv"
DEPARA = RAIZ / "dados" / "de_para.csv"

if len(sys.argv) > 2:          # python3 main.py <lancamentos> <de_para>
    ENTRADA, DEPARA = Path(sys.argv[1]), Path(sys.argv[2])
SAIDA = RAIZ / "saida"


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def carregar_de_para(competencia):
    """De-para em tabela, com vigência — quem mantém plano de contas é a
    contabilidade, não o dev. Vale a regra mais recente até a competência."""
    mapa = {}
    for r in sorted(ler(DEPARA), key=lambda r: r["vigencia_inicio"]):
        if date.fromisoformat(r["vigencia_inicio"]) <= competencia:
            mapa[(r["historico"], r["tipo"])] = r["conta"]
    return mapa


def chave(r):
    """Idempotência: rodar o mesmo período duas vezes não duplica nada."""
    bruto = f"{r['lote']}|ERP|{r['documento']}|{r['seq']}"
    return hashlib.sha1(bruto.encode()).hexdigest()[:12]


def validar(linhas, mapa):
    """Valida ANTES de gerar. Arquivo inválido descoberto na importação
    custa duas vezes, e já sob prazo."""
    erros = []

    por_lote = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for r in linhas:
        v = Decimal(r["valor"])
        por_lote[r["lote"]][0 if r["tipo"] == "D" else 1] += v

    for lote, (deb, cred) in sorted(por_lote.items()):
        if deb != cred:
            erros.append(
                f"lote {lote}: partida dobrada não fecha — "
                f"débito {deb} x crédito {cred} (dif. {deb - cred})"
            )

    for r in linhas:
        if (r["historico"], r["tipo"]) not in mapa:
            erros.append(
                f"doc {r['documento']} seq {r['seq']}: sem de-para para "
                f"'{r['historico']}' ({r['tipo']}) — processo para, não vai "
                f"para conta de ajuste"
            )
    return erros


def gerar(linhas, mapa, competencia):
    SAIDA.mkdir(exist_ok=True)
    destino = SAIDA / f"contabil_{competencia:%Y%m}.csv"
    vistos = set()
    n = 0
    with open(destino, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["chave", "data", "conta", "tipo", "valor", "historico", "cc"])
        for r in linhas:
            k = chave(r)
            if k in vistos:
                continue
            vistos.add(k)
            w.writerow([
                k, r["data"].replace("-", ""), mapa[(r["historico"], r["tipo"])],
                r["tipo"], f"{Decimal(r['valor']):.2f}".replace(".", ","),
                r["historico"], r["centro_custo"],
            ])
            n += 1
    return destino, n


def main():
    competencia = date(2026, 8, 1)
    linhas = ler(ENTRADA)
    mapa = carregar_de_para(competencia)

    print(f"lidos {len(linhas)} lançamentos · competência {competencia:%m/%Y}\n")

    erros = validar(linhas, mapa)
    if erros:
        print(f"VALIDAÇÃO FALHOU — {len(erros)} problema(s), nada foi gerado:\n")
        for e in erros:
            print(f"  · {e}")
        print("\nCorrija na origem e rode de novo.")
        return 1

    destino, n = gerar(linhas, mapa, competencia)
    print(f"OK — {n} linhas em {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
