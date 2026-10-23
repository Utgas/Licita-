#!/usr/bin/env python3
"""Fase 12 - a validação do M03 e do M04 fica no repositório (decisão 0008, 23/10/2026).

Uso: python3 -I f12_validacao_repo.py <matrizes/v1 do repositório> <pasta_Matrizes_v1>

Copia as colunas validacao e comentario_validacao do M03 e do M04 do repositório para os CSV locais, pela coluna id,
antes de regenerar as matrizes. Os geradores preservam essas colunas (comum.gravar_csv), então a entrega nova sai com
a validação igual à do repositório. ID do repositório que não existe mais localmente para a execução com erro.
"""
import csv
import sys
from pathlib import Path

COLS = ("validacao", "comentario_validacao")


def ler(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig", newline="")))


def main():
    repo, local = Path(sys.argv[1]), Path(sys.argv[2])
    for nome in ("M03_notas_explicativas.csv", "M04_wizard.csv"):
        r_rows = {r["id"]: r for r in ler(repo / nome)}
        l_rows = ler(local / nome)
        ids = {r["id"] for r in l_rows}
        faltam = [i for i, r in r_rows.items() if any(r.get(c) for c in COLS) and i not in ids]
        if faltam:
            raise SystemExit(f"{nome}: linhas validadas no repositório que não existem mais: {faltam}")
        n = 0
        for r in l_rows:
            fonte = r_rows.get(r["id"])
            if fonte:
                for c in COLS:
                    if r.get(c, "") != fonte.get(c, ""):
                        r[c] = fonte.get(c, "")
                        n += 1
        with open(local / nome, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(l_rows[0].keys()), quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(l_rows)
        cont = sum(1 for r in l_rows if r.get("validacao"))
        print(f"{nome}: {n} campos copiados do repositório; linhas com validacao preenchida: {cont}")


if __name__ == "__main__":
    main()
