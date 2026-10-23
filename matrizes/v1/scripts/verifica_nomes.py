#!/usr/bin/env python3
"""Teste de aceite 7 - nenhum nome de pessoa do corpus aparece nas matrizes.

Uso: python3 -I verifica_nomes.py <pasta_texto> <arquivo_ou_pasta_de_matrizes> [...]

1. Monta, em memoria, a lista de nomes de pessoas do corpus a partir de:
   - linhas em maiusculas dos blocos de assinatura (secoes 'Responsaveis');
   - coluna 'Responsavel' da secao 3 (Area requisitante) dos ETPs;
   - campo 'Editado por' das Informacoes Basicas dos TRs;
   - nomes que aparecem em nomes de arquivo da base (passados por --arquivos).
2. Procura cada nome completo e cada sobrenome distintivo (>= 5 letras, fora de lista de palavras
   comuns) nos arquivos de saida, sem diferenciar maiusculas e acentos.
A lista de nomes nunca e gravada em disco; os achados saem mascarados (inicial + ***).
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

COMUNS = set("""
ASSINOU ELETRONICAMENTE DESPACHO MEMBRO COMISSAO CONTRATACAO CHEFE CHEGE SECAO SETOR DIVISAO AUXILIAR EQUIPE
PLANEJAMENTO AUTORIDADE COMPETENTE ORDENADOR ORDENADORA DESPESAS DEPOSITO MATERIAL CIRURGICO MONTAGEM
ADMINISTRATIVA PROCESSO RADIOLOGIA MEDICINA SUBDIVISAO FARMACIA HOSPITAL CENTRAL EXERCITO BASE COMPLEXO SAUDE
POLICLINICA MILITAR GERAL JANEIRO NITEROI RESENDE PRAIA VERMELHA TODAS ASSINATURAS ELETRONICAS SEGUEM HORARIO
OFICIAL BRASILIA RESPONSAVEIS RESPONSAVEL REQUISITANTE AREA FISCAL TECNICO ADMINISTRATIVO GESTOR CONTRATO
ESTUDO TECNICO PRELIMINAR TERMO REFERENCIA ANEXO DECRETO LISTA ANEXOS ATENCAO APENAS ARQUIVOS FORMATOS
SANTOS SILVA SOUZA OLIVEIRA PEREIRA COSTA RODRIGUES ALMEIDA NASCIMENTO LIMA ARAUJO CARVALHO GOMES
MARTINS ROCHA RIBEIRO ALVES MONTEIRO MENDES BARROS FREITAS BARBOSA PINTO MOURA CAVALCANTI DIAS CASTRO CAMPOS
CARDOSO TEIXEIRA CORREIA MOREIRA
DE DA DO DOS DAS E PARA COM APOIO AQUISICAO MEDICO HOSPITALAR MANUTENCAO TRANSPORTE ALMOXARIFADO CLINICA
CIRURGIA URGENCIA PRONTO ATENDIMENTO ENFERMAGEM LABORATORIO ODONTOLOGIA SERVICO DIRETORIA TENENTE CORONEL
CAPITAO MAJOR SARGENTO
""".split())
# Sobrenomes muito comuns ficam fora da busca isolada (gerariam falso positivo), mas entram na busca
# do nome completo.


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).upper().strip()


def nomes_do_corpus(pasta_texto):
    nomes = set()
    for d in Path(pasta_texto).iterdir():
        if not d.is_dir():
            continue
        txt = (d / "_completo.txt").read_text(encoding="utf-8", errors="replace") if (d / "_completo.txt").exists() else ""
        # assinaturas: linha so com palavras em maiusculas (2 a 7 palavras), apos 'Responsáveis'
        for bloco in re.split(r"\n\s*\d{1,2}\.\s+Responsáveis", txt)[1:]:
            for linha in bloco.splitlines()[:40]:
                t = linha.strip()
                if re.fullmatch(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ' ]{8,80}", t) and 2 <= len(t.split()) <= 7:
                    nomes.add(norm(t))
        # secao 3 (Area requisitante): nomes em maiusculas, nomes capitalizados e posto + nome de guerra
        for m in re.finditer(r"\n\s*3\.\s+Área requisitante(.*?)\n\s*4\.\s+Descrição", txt, flags=re.S | re.I):
            bloco = m.group(1).replace("Área Requisitante", " ").replace("Responsável", " ")
            for cand in re.findall(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-záéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]+(?:\s+(?:(?:da|de|do|dos|das|DA|DE|DO|DOS|DAS)\s+)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-záéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]+){1,6}", bloco):
                nomes.add(norm(cand))
            for cand in re.findall(r"\b(?:CEL|Cap|Ten|MAJ|SGT|Sgt|TC)\b\.?\s+(?:R1\s+)?([A-ZÁÉÍÓÚ][a-záéíóúâêôãõç]{3,})\b", bloco):
                # nome de guerra isolado (posto + sobrenome): entra como nome a procurar
                nomes.add("§" + norm(cand))
        # TR: 'Editado por' -> nome em maiusculas na linha de valores
        for m in re.finditer(r"Editado por.*\n(.+)\n?(.*)", txt):
            for linha in (m.group(1), m.group(2)):
                for cand in re.findall(r"(?<![A-Z])([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,}(?: (?:DE |DA |DOS |DO |DI )?[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,}){1,5})", linha):
                    c = norm(cand)
                    if not any(w in c for w in ("BASE ADMINISTRATIVA", "COMPLEXO", "SAUDE", "CONCLUIDO", "ASSINADO")):
                        nomes.add(c)
        # DFD em formato próprio (ex.: PMPV): responsável pela demanda, equipe com CPF e linhas de assinatura com posto
        for m in re.finditer(r"Responsável pela Demanda:\s*(?:[A-Z][a-z]{1,4}\.?\s+){0,2}([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,}(?: [A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}){1,5})", txt):
            nomes.add(norm(m.group(1)))
        for m in re.finditer(r"(?m)^\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-záéíóúâêôãõç]+(?: (?:de |da |do |dos |das )?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-záéíóúâêôãõç]+){1,6})\s*-\s*\d{11}\b", txt):
            nomes.add(norm(m.group(1)))
        for m in re.finditer(r"(?m)^\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,}(?: [A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}){1,6})\s*[-–]\s*(?:Cap|Cel|Maj|Ten|TC|Sgt|Gen)\b", txt):
            nomes.add(norm(m.group(1)))
    isolados = {n[1:] for n in nomes if n.startswith("§")}
    completos = {n for n in nomes if not n.startswith("§") and len(n) >= 8 and not set(n.split()) <= COMUNS}
    return completos | isolados


REPO_COLS = ("validacao", "comentario_validacao")
AVISOS = []


def textos_saida(caminhos):
    for c in caminhos:
        p = Path(c)
        arquivos = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.suffix in (".csv", ".md", ".py", ".txt", ".json"))
        for a in arquivos:
            txt = a.read_text(encoding="utf-8-sig", errors="replace")
            if a.suffix == ".csv" and REPO_COLS[0] in txt.split("\n", 1)[0]:
                # validacao e comentario_validacao vêm do repositório (f12, P33): são registros de quem valida,
                # não texto copiado do corpus, e não podem ser alterados aqui; ficam fora da busca e saem como aviso
                linhas = list(csv.DictReader(txt.splitlines()))
                for r in linhas:
                    for c in REPO_COLS:
                        if (r.get(c) or "").strip():
                            AVISOS.append((a.name, r.get("id", ""), c, r[c]))
                            r[c] = ""
                txt = "\n".join(",".join(v or "" for v in r.values()) for r in linhas)
            yield a, txt


def main():
    pasta_texto, saidas = sys.argv[1], sys.argv[2:]
    nomes = nomes_do_corpus(pasta_texto)
    tokens = set()
    for n in nomes:
        for w in n.split():
            if len(w) >= 5 and w not in COMUNS:
                tokens.add(w)
    print(f"nomes de pessoas identificados no corpus: {len(nomes)}; sobrenomes distintivos: {len(tokens)}")
    # toda palavra de nome é mascarada no contexto impresso, para o relatório não vazar o nome vizinho
    partes = sorted({w for n in nomes for w in n.split() if len(w) >= 3}, key=len, reverse=True)

    def mascara(ctx):
        for w in partes:
            ctx = re.sub(rf"\b{re.escape(w)}\b", w[0] + "***", ctx)
        return ctx
    achados = 0
    for arq, txt in textos_saida(saidas):
        t = norm(txt)
        for n in nomes:
            if re.search(rf"\b{re.escape(n)}\b", t):
                achados += 1
                print(f"NOME COMPLETO em {arq.name}: {n[0]}***")
        for w in tokens:
            for m in re.finditer(rf"\b{re.escape(w)}\b", t):
                achados += 1
                ctx = mascara(t[max(0, m.start() - 30):m.end() + 30])
                print(f"SOBRENOME em {arq.name}: ...{ctx}...")
    # números de CPF (formatados ou não) nunca podem aparecer nas saídas
    for arq, txt in textos_saida(saidas):
        for m in re.finditer(r"(?<![\d./-])\d{3}\.\d{3}\.\d{3}-\d{2}(?![\d/])|(?<![\d./-])\d{11}(?![\d./-])", txt):
            achados += 1
            print(f"POSSÍVEL CPF em {arq.name}: {m.group(0)[:3]}********")
    vistos = set()
    for arq, rid, col, val in AVISOS:
        t = norm(val)
        if (arq, rid, col) in vistos:
            continue
        vistos.add((arq, rid, col))
        if any(re.search(rf"\b{re.escape(w)}\b", t) for w in tokens | nomes):
            print(f"AVISO (coluna do repositório, preservada; não conta como achado) em {arq} {rid} {col}: {mascara(t[:60])}")
    print(f"achados: {achados}")
    sys.exit(1 if achados else 0)


if __name__ == "__main__":
    main()
