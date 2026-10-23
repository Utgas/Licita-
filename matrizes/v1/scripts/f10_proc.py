#!/usr/bin/env python3
"""Fase 10, tarefa 8: troca os números de processo (NUP) do corpus por PROC-01, PROC-02 etc.

Uso: python3 -I f10_proc.py <pasta_Matrizes_v1> <correspondencia.csv fora do repositório> [arquivos extras ...]

A numeração segue a ordem de primeira aparição no M00. Troca no M00, no perguntas_abertas.md e nos arquivos extras
(scripts que tinham o número escrito). A correspondência PROC-xx -> número real vai só para o CSV indicado, que não
entra no pacote. Rodar de novo não muda nada: lê a correspondência existente e só acrescenta números novos.
Os NUPs citados nas notas do modelo AGU (M03, pareceres e despachos da AGU) não são processos do corpus e ficam.
"""
import csv
import re
import sys
from pathlib import Path

NUP = re.compile(r"\b\d{5}\.\d{6}/\d{4}-\d{2}\b|\b\d{17}\b")  # com e sem máscara
FICTICIO = "00000.000000/0000-00"


def main():
    pasta, corr = Path(sys.argv[1]), Path(sys.argv[2])
    extras = [Path(x) for x in sys.argv[3:]]
    mapa = {}
    if corr.exists():
        for r in csv.DictReader(open(corr, encoding="utf-8-sig")):
            mapa[r["numero_real"]] = r["codigo"]
    m00 = pasta / "M00_inventario.csv"
    texto = open(m00, encoding="utf-8-sig", newline="").read()
    for n in NUP.findall(texto):
        if n != FICTICIO and n not in mapa:
            mapa[n] = f"PROC-{len(mapa) + 1:02d}"
    alvos = [m00, pasta / "perguntas_abertas.md"] + extras
    trocas = {}
    for f in alvos:
        t = open(f, encoding="utf-8-sig" if f.suffix == ".csv" else "utf-8", newline="").read()
        novos = [n for n in NUP.findall(t) if n != FICTICIO and n not in mapa]
        if novos:
            raise SystemExit(f"{f.name}: número de processo fora do M00: {novos}")
        n_antes = len([n for n in NUP.findall(t) if n in mapa])
        t2 = NUP.sub(lambda mt: mapa.get(mt.group(0), mt.group(0)), t)
        with open(f, "w", encoding="utf-8-sig" if f.suffix == ".csv" else "utf-8", newline="") as fh:
            fh.write(t2)
        trocas[f.name] = n_antes
    corr.parent.mkdir(parents=True, exist_ok=True)
    with open(corr, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["codigo", "numero_real"])
        for n, c in sorted(mapa.items(), key=lambda x: x[1]):
            w.writerow([c, n])
    print(f"processos: {len(mapa)}; trocas por arquivo: {trocas}")


if __name__ == "__main__":
    main()
