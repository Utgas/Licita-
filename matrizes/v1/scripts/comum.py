#!/usr/bin/env python3
"""Funções comuns aos scripts de análise do Licita+ (gravação de CSV e preservação da revisão do usuário)."""
import csv
from pathlib import Path

REVISAO = ("validacao", "comentario_validacao")


def ler_csv(caminho):
    p = Path(caminho)
    if not p.exists():
        return []
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def gravar_csv(caminho, colunas, linhas, preservar=REVISAO, chave="id"):
    """Grava CSV (UTF-8 com BOM, vírgula, todo campo entre aspas).

    As colunas em `preservar` (revisão do usuário) são mantidas do arquivo anterior, pela chave, quando a linha
    nova as traz vazias. Assim, regenerar uma matriz não apaga a validação feita no xlsx e já importada.
    """
    antigas = {r.get(chave): r for r in ler_csv(caminho)}
    for l in linhas:
        a = antigas.get(l.get(chave), {})
        for c in preservar:
            if c in colunas and not l.get(c):
                l[c] = a.get(c, "")
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        w.writeheader()
        for l in linhas:
            w.writerow({c: l.get(c, "") for c in colunas})
