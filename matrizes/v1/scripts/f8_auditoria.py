#!/usr/bin/env python3
"""Fase 8 - Auditoria das matrizes 01 (TR AGU) e 02 (ETP Digital), rascunhos da base, contra o M02, o M01 e o M07.

Uso: python3 -I f8_auditoria.py <pasta_Documentos> <pasta_Matrizes_v1>

Medições por script:
  Matriz 01: cada linha de tabela com '#' numérico; o 'Conteúdo Modelo AGU' entre crases é comparado com o texto
  literal dos blocos do M02 (trechos separados por '[...]' precisam estar contidos num bloco). Classes: LITERAL,
  LITERAL_COM_CORTES, PARAFRASE (semelhança >= 0,5 com algum bloco), SEM_CORRESPONDENCIA, SEM_TEXTO_DO_MODELO.
  Tipo da linha (TF, OP...) comparado com a formatação do bloco casado.
  Matriz 02: secões x M01, marcação 'Obrigatório' x art. 18, § 2º (incisos I, IV, VI, VIII e XIII), referências a itens
  do TR inexistentes no modelo DEZ/2025 e 'Base Normativa' x M07.
O texto da auditoria cita linhas dos arquivos auditados; as conclusões são minhas (INFERIDO) e as contagens, do script.
"""
import csv
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citacoes import extrair  # noqa: E402
from normas import identidades  # noqa: E402


def ler(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def norm(t):
    return re.sub(r"\s+", " ", re.sub(r"[“”\"'`*]", "", t.lower())).strip(" .;:")


def tabelas(arq):
    rows, header = [], None
    for i, l in enumerate(open(arq, encoding="utf-8"), 1):
        if not l.startswith("|"):
            continue
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if cells and cells[0] == "#":
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if header and re.match(r"^\d+(\.\d+)*$", cells[0]):
            rows.append((i, dict(zip(header, cells))))
    return rows


def main():
    doc, pasta = Path(sys.argv[1]), Path(sys.argv[2])
    a01, a02 = doc / "Matriz/01_Matriz_TR_AGU_Aquisicoes.md", doc / "Matriz/02_Matriz_ETP_Digital_Lei14133.md"
    m02 = ler(pasta / "M02_tr_blocos.csv")
    m01 = ler(pasta / "M01_etp_campos.csv")
    m07 = {r["chave"]: r for r in ler(pasta / "M07_normas.csv")}
    blocos = [(r["id"], norm(r["texto_literal"]), r) for r in m02 if r["item_modelo"] != "OU"]
    nao_nota = [b for b in blocos if b[2]["formatacao"] != "NOTA_EXPLICATIVA"]

    # ------------------------------------------------------------------ Matriz 01
    r1 = tabelas(a01)
    cls, cobertos, conflitos, exemplos = Counter(), set(), [], {}
    for ln, d in r1:
        cont = d.get("Conteúdo Modelo AGU", "")
        frags = re.findall(r"`([^`]+)`", cont)
        tipo = d.get("Tipo", "").replace("*", "").strip()
        if not frags:
            cls["SEM_TEXTO_DO_MODELO"] += 1
            exemplos.setdefault("SEM_TEXTO_DO_MODELO", []).append(f"linha {ln} ({d['#']})")
            continue
        txt = " ".join(frags)
        partes = [norm(p) for p in re.split(r"\[\.\.\.\]|\[…\]", txt) if len(norm(p)) >= 12]
        achou = [next((b for b in blocos if p in b[1]), None) for p in partes]
        if partes and all(achou):
            c = "LITERAL_COM_CORTES" if re.search(r"\[\.\.\.\]|\[…\]", txt) else "LITERAL"
            cobertos.update(h[0] for h in achou)
            alvo, razao = achou[0][2], 1.0
        else:
            razao, bid = max((difflib.SequenceMatcher(None, norm(txt), b[1]).ratio(), b[0]) for b in blocos)
            c = "PARAFRASE" if razao >= 0.5 else "SEM_CORRESPONDENCIA"
            alvo = next(b[2] for b in blocos if b[0] == bid) if razao >= 0.7 else None
        cls[c] += 1
        exemplos.setdefault(c, []).append(f"linha {ln} ({d['#']})")
        if alvo is not None:
            if tipo == "TF" and alvo["formatacao"] != "PRETO":
                conflitos.append(f"linha {ln} ({d['#']}): tipo TF, mas {alvo['id']} é {alvo['formatacao']} "
                                 f"(condição no M02: {alvo['condicao_inclusao'][:90]})")
            if "OP" in tipo and alvo["formatacao"] == "PRETO" and not alvo["condicao_inclusao"].startswith("SE"):
                conflitos.append(f"linha {ln} ({d['#']}): tipo {tipo}, mas {alvo['id']} é texto em preto incondicional")
    til = sum(l.count("~") for l in open(a01, encoding="utf-8"))
    nota = len(re.findall(r"(?i)\bnotas?\b", a01.read_text(encoding="utf-8")))

    # ------------------------------------------------------------------ Matriz 02
    r2 = tabelas(a02)
    itens = {r["item_modelo"].strip().rstrip(".") for r in m02}
    refs_inex = []
    for ln, d in r2:
        tr = d.get("Transposição para o TR", "")
        nums = re.findall(r"(?<![\d.])(\d{1,2}(?:\.\d{1,2}){0,3})(?![\d.])", tr)
        inex = [n for n in nums if n not in itens]
        if inex:
            refs_inex.append(f"linha {ln} ({d['#']} {d.get('Campo no ETP Digital', '').strip('*')}): {', '.join(inex)}")
    obrig = Counter()
    for ln, d in r2:
        sec = d["#"].split(".")[0]
        if d.get("Caráter Legal", "").startswith("Obrigatório"):
            obrig[sec] += 1
    secoes_obrig_m02 = sorted(obrig, key=int)
    # artigos citados no modelo ou nas notas (M07.dispositivos_citados) e artigos conferidos em fonte oficial
    def arts(txt):
        return {int(x) for x in re.findall(r"(?i)\bart(?:igo)?s?\.?\s*(\d+)", txt)}
    conferidos = {"LEI-14133-2021": {18}, "IN-SEGES-ME-58-2022": {8, 9, 14}}
    arts_base = {}
    m03 = ler(pasta / "M03_notas_explicativas.csv")
    for celula in [r["normas"] for r in m02] + [r["citacoes"] for r in m03]:
        ultima = None
        for c in [x.strip() for x in celula.split(";") if x.strip()]:
            ids = identidades(c)
            for k in ([i[0] for i in ids] or ([ultima] if ultima else [])):
                arts_base.setdefault(k, set()).update(arts(c))
            if ids:
                ultima = ids[-1][0]
    bases = []
    for ln, d in r2:
        b = d.get("Base Normativa", "").strip()
        if not b:
            continue
        itens_b = []
        for parte in re.split(r"\s*(?:/|\be\b|;)\s*(?=(?:Lei|IN|Dec|RDC|Decreto|Ajuste|Protocolo|Conama|Súmula|Art|Boas|Normas|Prática))", b):
            ids = [i for c in extrair(parte) for i in identidades(c)]
            if not ids and re.search(r"(?i)\bart\.", parte):
                ids = [("LEI-14133-2021", "Lei nº 14.133/2021 (lei não nomeada; presumida)", "", "", "", "")]
            if not ids:
                itens_b.append(f"'{parte}': sem norma identificável")
                continue
            for i in ids:
                r7 = m07.get(i[0])
                base = r7 is not None and bool(set(r7["origem"].split("; ")) & {"MODELO_AGU", "NOTA_AGU"})
                a = arts(parte)
                a_base = arts_base.get(i[0], set())
                a_ok = a <= (a_base | conferidos.get(i[0], set()))
                if not base and i[0] not in conferidos:
                    itens_b.append(f"{i[1]}: fora da base e não conferida")
                elif a and not a_ok:
                    falta = sorted(a - a_base - conferidos.get(i[0], set()))
                    itens_b.append(f"{i[1]}: norma na base, mas art. {', '.join(map(str, falta))} não citado no modelo "
                                   f"nem conferido")
                else:
                    itens_b.append(f"{i[1]}: na base")
        bases.append((ln, d["#"], b, itens_b))
    secoes = [l.strip() for l in open(a02, encoding="utf-8") if re.match(r"^## \d+\.", l)]

    # ------------------------------------------------------------------ relatório
    out = ["# Auditoria das matrizes 01 e 02 (Fase 8)", "",
           "Arquivos auditados: `Matriz/01_Matriz_TR_AGU_Aquisicoes.md` e `Matriz/02_Matriz_ETP_Digital_Lei14133.md` "
           "(rascunhos, nível 4 da hierarquia de fontes). Referências: M02 (texto literal do modelo DEZ/2025), M01 (campos do "
           "ETP Digital), M03 (notas), M07 (normas). Contagens geradas por `scripts/f8_auditoria.py`; conclusões INFERIDAS. "
           "Os desvios principais também estão no M09 (DV-31 a DV-34).", "",
           "## Conclusão", "",
           "As duas matrizes servem como inventário de assuntos, não como fonte do sistema. A matriz 01 não copia o texto do "
           "modelo na maior parte das linhas e não registra as notas explicativas; a matriz 02 mistura o ETP Digital com "
           "práticas de um TR específico (numeração do TR 117/2025), marca como obrigatórias seções que a lei não exige e deixa "
           "de marcar uma que exige, e cita normas que não estão na base nem foram conferidas. As matrizes v1 substituem as "
           "duas: M02 e M03 no lugar da matriz 01; M01, M06 e M11 no lugar da matriz 02.", "",
           "## Matriz 01: TR AGU", "",
           f"- Linhas de campo (tabelas com '#'): {len(r1)}.",
           f"- Classificação do 'Conteúdo Modelo AGU' contra o texto literal do M02: "
           + "; ".join(f"{k} {v}" for k, v in sorted(cls.items())) + ".",
           f"- Blocos do M02 (sem notas e separadores) cujo texto aparece em alguma linha: {len(cobertos)} de {len(nao_nota)}. "
           f"As demais linhas descrevem blocos sem copiar o texto ('Bloco completo sobre procedimento de amostra', 'Blocos "
           f"extensos sobre seguro-garantia...'), o que impede usar a matriz como fonte literal.",
           f"- Ocorrências da palavra 'nota': {nota}. O modelo DEZ/2025 tem 102 notas explicativas (M03). Ver DV-31.",
           f"- Ocorrências de '~' (estimativa): {til}, inclusive no resumo estatístico final ('~47% texto fixo'). Ver DV-33.",
           "- Arquivo-fonte declarado: `media_1792606488039_644bd1c3.docx`, sem hash; 30 dos 35 intervalos 'Linhas' batem pelo "
           "título com o docx DEZ/2025 e 5 pedem leitura (logs/f0_conferencias.txt, seção 4). Ver DV-32.",
           "- Tipo da linha contra a formatação do modelo (só nas linhas com texto casado):"]
    out += [f"  - {c}" for c in conflitos] or ["  - nenhum conflito nas linhas casadas"]
    out += ["- Pontos lidos linha a linha:",
            "  - Linha 48 (1.3.2, bem de luxo): marcada como texto fixo 'sempre presente'; no modelo o item é vermelho itálico e "
            "a NE-006 o liga ao bem de consumo (TR-1.4).",
            "  - Linha 130 (4.7.1, cota de ME/EPP): 'reserva de 25%'. O modelo e a NE-022 falam em cota de até 25%; o "
            "Decreto 8.538/2015, art. 8º, também ('até vinte e cinco por cento', conferido no planalto.gov.br).",
            "  - Linhas 54 a 56 (vigência): o texto da opção B ('prorrogável por até 10 anos') e o da opção C ('improrrogável') "
            "não estão no corpo do modelo com essa redação; as opções reais são TR-1.6/TR-1.7 e TR-1.8.",
            "  - Linhas 158, 181, 197, 204 e 212: trechos que não correspondem a nenhum bloco do modelo (prazos e percentuais "
            "reescritos).", "",
            "## Matriz 02: ETP Digital", "",
            f"- Seções: {len(secoes)} ({'; '.join(s[3:] for s in secoes)}).",
            "- A seção 12 da matriz é 'Justificativas Técnicas Específicas / Qualificação & Amostra'; no ETP Digital e nos ETPs "
            "do corpus a seção 12 é 'Resultados Pretendidos' ou 'Benefícios a serem alcançados com a contratação' (M01 ETP-12.01; "
            "P07). A seção 16 (Responsáveis) não existe na matriz; as assinaturas estão em 15.3.",
            "- O campo 3.3 'Equipe de Planejamento da Contratação' não é campo do ETP Digital nos ETPs do corpus (M01 tem "
            "ETP-03.01 e ETP-03.02) e aponta para 'Cláusula 22 do TR', que não existe no modelo.",
            f"- Seções com linha marcada 'Obrigatório': {', '.join(secoes_obrig_m02)}. O art. 18, § 2º, exige os incisos I, IV, "
            "VI, VIII e XIII (seções 2, 7, 8, 9 e 15 do ETP Digital). A matriz não marca a seção 9 (parcelamento, inciso VIII) e "
            "marca a 6 (solução, inciso VII), a 1 e a 3 (dados de identificação) e o 6.3 (índice de reajuste, que não é elemento "
            "do ETP). O M01 marca os cinco incisos (teste 6).",
            "- A linha 62 (4.1) fixa 'Validade mínima de 50% na data da entrega' como 'regra padrão hospitalar militar'. A "
            "decisão de 22/10/2026 (P21) é sem valor sugerido: a validade vem da CK-C-14.2, item a item.",
            f"- Referências a itens do TR que não existem no modelo DEZ/2025 ({len(refs_inex)} linhas); a numeração é a do TR "
            "117/2025:"]
    out += [f"  - {x}" for x in refs_inex]
    out += ["- Coluna 'Base Normativa' contra a base (norma e artigo citados no modelo AGU ou nas notas, ou conferidos em fonte "
            "oficial; a conferência é no nível do artigo, sem parágrafo, inciso ou alínea):"]
    for ln, n, b, itens_b in bases:
        out.append(f"  - linha {ln} ({n}) '{b}': " + "; ".join(itens_b))
    out += ["- Linha 44 (2.3) fundamenta 'bem comum' no Decreto 10.024/2019, e a linha 168 (14.1) cita a IN SLTI/MP "
            "01/2010: normas do regime anterior, situação não conferida (DV-34; VAL-004).",
            "- O fecho da matriz afirma que 'mais de 80% do Termo de Referência é preenchido automaticamente'. Não há contagem "
            "que sustente o número; o M06 classifica a origem de cada bloco do M02 e é a medida a usar.", "",
            "## O que foi aproveitado", "",
            "- Da matriz 01: a legenda de tipos (TF, EU, IA, OP, TB), mantida no M02 com regra explícita por formatação.",
            "- Da matriz 02: as colunas 'regra de preenchimento e anti-alucinação' e 'transposição para o TR', que viraram "
            "M01.regra_anti_alucinacao, M01.destino_tr e o M06.",
            "- Da matriz 02, como tema de cláusula setorial (M08), não como texto: comodato (4.5), rastreabilidade (4.3), "
            "logística e transporte (4.4) e regime de consignação (6.4, sem a norma citada, que não foi conferida).", ""]
    (pasta / "auditoria_matrizes_01_02.md").write_text("\n".join(out), encoding="utf-8")
    print(f"Matriz 01: {len(r1)} linhas; {dict(cls)}; blocos cobertos por texto {len(cobertos)} de {len(nao_nota)}; "
          f"conflitos de tipo {len(conflitos)}; '~' {til}; 'nota' {nota}")
    print(f"Matriz 02: {len(r2)} linhas; seções obrigatórias marcadas {secoes_obrig_m02}; refs inexistentes {len(refs_inex)}; "
          f"bases {len(bases)} ({sum(1 for b in bases if any('na base' not in x for x in b[3]))} com item a conferir)")


if __name__ == "__main__":
    main()
