"""Fase 10, tarefa extra: inventário dos arquivos do repositório auxiliar ctresb/leis (commit 15eb09b) que
correspondem a normas do M07. Lê o cabeçalho YAML de cada arquivo com `git show` num clone parcial e grava
log_fase10_repo_leis.md. Só arquivos com versao_texto "compilada (texto vigente)" servem para localizar texto;
a situação vigente vem da fonte oficial (VERIF em f5_gerar_M07.py).
Uso: python3 -I f10_repo_leis.py CLONE CAMINHOS.txt SAIDA.md"""
import subprocess, sys
from pathlib import Path

COMMIT = "15eb09b"
clone, lista, saida = sys.argv[1], sys.argv[2], Path(sys.argv[3])
linhas = ["# Repositório auxiliar ctresb/leis no M07 (Fase 10)", "",
          f"Commit {COMMIT}618ff08a38c4dfee06a91bd139d093f5d (21/10/2026). Fonte auxiliar, nunca fonte de verdade.", "",
          "Regras: só `versao_texto: \"compilada (texto vigente)\"` (ou \"dados abertos do tribunal\" para súmulas do TCU) "
          "serve para localizar texto; `original` não foi usado; o arquivo da Lei 14.133 não foi usado; INs SEGES 58/2022, "
          "65/2021, 73/2022 e 81/2022 não estão no repositório e foram conferidas só no gov.br.", "",
          "| arquivo | versao_texto | revogada (cabeçalho) | uso |", "|---|---|---|---|"]
cont = {"usado": 0, "nao_usado": 0}
for cam in Path(lista).read_text(encoding="utf-8").split():
    txt = subprocess.run(["git", "-C", clone, "show", f"{COMMIT}:{cam}"], capture_output=True, text=True).stdout
    cab = {}
    if txt.startswith("---"):
        for l in txt.split("\n---", 1)[0].splitlines()[1:]:
            if ":" in l:
                k, v = l.split(":", 1)
                cab[k.strip()] = v.strip().strip('"')
    vt = cab.get("versao_texto", "(sem campo)")
    uso = "localizar dispositivo; situação conferida no Planalto" if vt == "compilada (texto vigente)" else "não usado"
    if "lei-10520-2002" in cam:
        uso = "não usado (já conferida no Planalto em 22/10/2026)"
    cont["usado" if not uso.startswith("não usado") else "nao_usado"] += 1
    linhas.append(f"| `{cam}` | {vt} | {cab.get('revogada', '')} | {uso} |")
linhas += ["", f"Total: {cont['usado'] + cont['nao_usado']} arquivos; usados: {cont['usado']}; não usados: {cont['nao_usado']}.",
           "", "Fora da lista: Constituição (`constituicao.md`, sem campo versao_texto), Circulares SUSEP 656 e 662/2022 "
           "(`publicação original`), RDCs Anvisa 16/2014 e 304/2019 e Resolução CMN 5.050/2022 (não encontradas)."]
saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
print(cont)
