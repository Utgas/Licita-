#!/usr/bin/env python3
"""Leitura estrutural dos checklists técnicos (docx) para o M11. Módulo de análise, não código do sistema.

Uso como script: python3 -I ck_ler.py <checklist.docx> <saida.json>
Uso como módulo: from ck_ler import ler_checklist

A partir do JSON do f1_modelo_estrutura (parágrafos em ordem, com tabela e célula), reconhece:
  seção     linha 'N. TÍTULO EM MAIÚSCULAS';
  pergunta  linha 'N.M. texto' (numeração digitada, não automática);
  opções    linha que começa com '☐' (várias opções na mesma linha, separadas por espaços ou quebras);
  orientação demais linhas de texto entre uma pergunta e a próxima (exceto 'Resposta:');
  campos    rótulos das tabelas de resposta com texto (ex.: 'Percentual utilizado');
  caixa     tabela de resposta de uma célula vazia logo depois de 'Resposta:'.
Partes sem número (cabeçalho, lista de anexos da seção 22, declaração da seção 23) viram itens com número próprio.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SECAO = re.compile(r"^(\d{1,2})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 ,/\-–()]+)$")
PERG = re.compile(r"^(\d{1,2}\.\d{1,2})\.\s+(.+)$", re.S)


def opcoes_da_linha(t):
    partes = [p.strip() for p in re.split(r"☐", t) if p.strip()]
    return [re.sub(r"\s+", " ", p).strip(" /") for p in partes]


def ler_checklist(json_modelo):
    m = json.load(open(json_modelo, encoding="utf-8"))
    itens = []
    secao = ("0", "CABEÇALHO")
    atual = None
    cab = []
    for p in m["paragrafos"]:
        t = p["texto"].strip()
        tab = p["tabela"]
        if not t:
            if tab is not None and atual is not None:
                atual["caixas"] += 1
            continue
        if tab is not None:
            rot = re.sub(r"\s+", " ", t).strip(" /")
            if atual is None and secao[0] == "0":
                cab.append((rot, p["n"]))
            elif atual is not None:
                atual["campos"].append(rot)
                atual["par_fim"] = p["n"]
            continue
        ms = SECAO.match(t)
        if ms and t == t.upper():
            secao = (ms.group(1), ms.group(2).strip())
            atual = None
            if secao[0] in ("22", "23"):
                atual = {"numero": secao[0], "secao": f"{secao[0]}. {secao[1]}", "pergunta": "", "opcoes": [],
                         "orientacoes": [], "campos": [], "caixas": 0, "par_ini": p["n"], "par_fim": p["n"], "sem_numero": True}
                itens.append(atual)
            continue
        mp = PERG.match(t)
        if mp:
            atual = {"numero": mp.group(1), "secao": f"{secao[0]}. {secao[1]}", "pergunta": re.sub(r"\s+", " ", mp.group(2)).strip(),
                     "opcoes": [], "orientacoes": [], "campos": [], "caixas": 0, "par_ini": p["n"], "par_fim": p["n"],
                     "sem_numero": False}
            itens.append(atual)
            continue
        if atual is None:
            continue
        atual["par_fim"] = p["n"]
        if t.startswith("☐"):
            atual["opcoes"] += opcoes_da_linha(t)
        elif t == "Resposta:":
            atual["tem_resposta"] = True
        elif t.startswith("Declaro que"):
            atual["pergunta"] = t
        elif atual.get("sem_numero") and not atual["pergunta"] and atual["numero"] == "22" and not t.startswith("Indique"):
            atual["orientacoes"].append(re.sub(r"\s+", " ", t))
        else:
            atual["orientacoes"].append(re.sub(r"\s+", " ", t))
    cab_itens = [{"numero": f"CAB.{k:02d}", "secao": "0. CABEÇALHO", "pergunta": rot, "opcoes": [], "orientacoes": [],
                  "campos": [], "caixas": 1, "par_ini": n, "par_fim": n, "sem_numero": True}
                 for k, (rot, n) in enumerate(cab, 1)]
    return cab_itens + itens


def main():
    docx, saida = sys.argv[1], sys.argv[2]
    tmp = Path(saida).with_suffix(".estrutura.json")
    script = Path(__file__).resolve().parent / "f1_modelo_estrutura.py"
    subprocess.run([sys.executable, "-I", str(script), docx, str(tmp)], check=True, capture_output=True)
    itens = ler_checklist(tmp)
    json.dump(itens, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{saida}: {len(itens)} itens")


if __name__ == "__main__":
    main()
