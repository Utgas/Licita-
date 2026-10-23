#!/usr/bin/env python3
"""Fase 0 - Lista os titulos de secao (padrao ETP Digital / TR Digital) por pagina.

Uso: python3 -I f0_secoes.py <pasta_texto_documento> [<pasta> ...]
Reconhece linhas do tipo "N. Titulo" (N de 1 a 30) com inicial maiuscula e sem ponto final,
que e o formato dos titulos de secao gerados pelo Compras.gov.br.
"""
import re
import sys
from pathlib import Path

PAT = re.compile(r"^\s{0,3}(\d{1,2})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n]{2,120})$")


def main():
    for d in sys.argv[1:]:
        d = Path(d)
        print(f"#### {d.name}")
        for f in sorted(d.glob("p[0-9][0-9][0-9].txt")):
            pg = int(f.stem[1:])
            for line in f.read_text(encoding="utf-8").splitlines():
                m = PAT.match(line)
                if m and not line.strip().endswith((".", ";", ",")) and len(line.strip()) < 110:
                    titulo = re.sub(r"\s{2,}.*$", "", m.group(2).strip())
                    print(f"  p{pg:>2}  {m.group(1):>2}. {titulo}")


if __name__ == "__main__":
    main()
