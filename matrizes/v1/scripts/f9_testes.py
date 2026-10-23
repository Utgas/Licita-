#!/usr/bin/env python3
"""Fase 9 - Testes de aceite 1 a 8 e conferências de formato, IDs, referências, domínios e JSON Logic (M00 a M11).

Uso: python3 -I f9_testes.py <pasta_Matrizes_v1> <f1_modelo.json> <pasta_Documentos> <pasta_texto> <saida.txt>

Testes do prompt (seção de aceite, reconstruída: ver README):
  1 cobertura dos parágrafos não vazios do modelo pelo M02;   2 as 102 notas ligadas a bloco existente;
  3 integridade dos IDs (únicos, no padrão, referências que existem);   4 toda norma citada de M01 a M11 está no M07;
  5 fonte e status preenchidos e no domínio;   6 incisos I, IV, VI, VIII e XIII obrigatórios no M01;
  7 nenhum nome de pessoa (verifica_nomes.py, rodado à parte; aqui só se lê o resultado no log);
  8 cada achado da seção 5 (lista reconstruída, 10 itens) aparece no M09 ou no M10.
Conferências adicionais: formato CSV, domínios fechados, JSON Logic (sintaxe, operadores e variáveis existentes),
M06 cobre o M02, M11 cobre os dois checklists com hash conferido, evidências do M08 literais no corpus, travessão
fora das colunas literais, simulação do wizard sem problema e controle negativo da simulação.
"""
import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citacoes import extrair  # noqa: E402
from normas import identidades  # noqa: E402

ARQS = {"M00": "M00_inventario.csv", "M01": "M01_etp_campos.csv", "M02": "M02_tr_blocos.csv",
        "M03": "M03_notas_explicativas.csv", "M04": "M04_wizard.csv", "M05": "M05_variaveis.csv",
        "M06": "M06_derivacao_etp_tr.csv", "M07": "M07_normas.csv", "M08": "M08_clausulas_setoriais.csv",
        "M09": "M09_desvios.csv", "M10": "M10_validacoes.csv", "M11": "M11_checklist.csv",
        "M12": "M12_parametros.csv"}
CHAVE = {"M00": "arquivo", "M06": "bloco_tr"}
PADRAO = {"M01": r"ETP-\d{2}\.\d{2}", "M02": r"TR-[A-Za-z0-9.\-]+", "M03": r"NE-\d{3}", "M04": r"WZ-\d{2}",
          "M05": r"VAR-\d{3}", "M06": r"TR-[A-Za-z0-9.\-]+", "M07": r"NRM-\d{3}", "M08": r"SET-\d{2}", "M09": r"DV-\d{2}",
          "M10": r"VAL-\d{3}", "M11": r"CK-[CPX]-(?:CAB\.\d{2}|\d{1,2}(?:\.\d{1,2})?)", "M12": r"PAR-\d{2}"}
LITERAIS = {"texto_literal", "texto_integral", "trecho_ancorado", "lacunas", "citacoes", "normas", "objeto_resumo", "pergunta",
            "opcoes", "orientacao", "evidencia_corpus", "evidencia_par_117", "evidencia_caso_67_23", "formas_citadas",
            "descricao", "condicao_expr", "liga_expr", "desliga_expr", "depende_de_expr", "calculo_expr",
            "condicional_expr", "preenche_expr", "sugere_expr", "revisao_expr", "grupo_ativo_expr", "leitura",
            "revisao_pergunta"}
STATUS = {"EXTRAIDO", "INFERIDO", "A_VERIFICAR"}
ID_RX = re.compile(r"\b(?:TR-[A-Za-z0-9.\-]+|ETP-\d{2}\.\d{2}|WZ-\d{2}|NE-\d{3}|VAR-\d{3}|SET-\d{2}|VAL-\d{3}|DV-\d{2}|"
                   r"NRM-\d{3}|CK-[CPX]-(?:CAB\.\d{2}|\d{1,2}(?:\.\d{1,2})?))")
# Achados da seção 5 do prompt (lista reconstruída do registro da Fase 0: logs/f0_conferencias.txt e P01 a P11)
ACHADOS_S5 = {1: "notas explicativas do modelo e ausência delas na matriz 01", 2: "arquivo-fonte e linhas da matriz 01",
              3: "estimativas ('~') na matriz 01", 4: "ETP 19/2026 com páginas ausentes",
              5: "pares ETP e TR, processos em branco e divergência ETP 67/2026 x TR 23/2026",
              6: "normas do regime anterior no corpus e na matriz 02", 7: "TRs feitos sobre versões anteriores do modelo",
              8: "validade mínima de 50% e 75% e contradição do ETP 99/2025",
              9: "participante de IRP que remete ao gerenciador (e ETP 99/2025 com texto próprio)",
              10: "nome e numeração da seção 12 do ETP"}


def ler(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))


def main():
    pasta, modelo_json, docs, texto, saida = map(Path, sys.argv[1:6])
    modelo = json.load(open(modelo_json, encoding="utf-8"))
    out, falhas = [], 0

    def reg(ok, msg):
        nonlocal falhas
        out.append(("OK    " if ok else "FALHA ") + msg)
        falhas += 0 if ok else 1

    M = {k: ler(pasta / v) for k, v in ARQS.items()}
    # ------------------------------------------------------------ formato
    for k, v in ARQS.items():
        bruto = (pasta / v).read_bytes()
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(M[k][0].keys()), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(M[k])
        igual = buf.getvalue() == open(pasta / v, encoding="utf-8-sig", newline="").read()
        reg(bruto.startswith(b"\xef\xbb\xbf") and igual, f"{v}: UTF-8 com BOM, vírgula, todos os campos entre aspas")
    # ------------------------------------------------------------ teste 3: IDs
    ids = {}
    for k in ARQS:
        if k == "M00":
            continue
        col = CHAVE.get(k, "id")
        lista = [r[col] for r in M[k]]
        rep = [i for i, c in Counter(lista).items() if c > 1]
        fora = [i for i in lista if not re.fullmatch(PADRAO[k], i)]
        reg(not rep and not fora, f"teste 3: {k} com {len(lista)} IDs únicos e no padrão"
            + (f" | repetidos {rep[:5]} | fora {fora[:5]}" if rep or fora else ""))
        ids[k] = lista
    todos = set().union(*[set(v) for k, v in ids.items() if k != "M06"])
    lista02 = ids["M02"]
    ordem02 = {k: i for i, k in enumerate(lista02)}
    quebradas = []
    for k in ARQS:
        for r in M[k]:
            rid = r.get(CHAVE.get(k, "id"))
            for col, val in r.items():
                if col in LITERAIS or col in ("fonte", "id", "bloco_tr", "arquivo") or not val:
                    continue
                for m in re.finditer(r"(TR-[A-Za-z0-9.\-]+)\.\.(TR-[A-Za-z0-9.\-]+)", val):
                    a, b = m.group(1).rstrip(".-"), m.group(2).rstrip(".-")
                    if a not in ordem02 or b not in ordem02 or ordem02[a] > ordem02[b]:
                        quebradas.append(f"{k}:{rid}.{col} faixa {a}..{b}")
                for ref in ID_RX.findall(val.replace("..", " ")):
                    ref = ref.rstrip(".-")
                    if ref not in todos:
                        quebradas.append(f"{k}:{rid}.{col} -> {ref}")
    reg(not quebradas, f"teste 3: referências cruzadas entre M00 e M11: {len(quebradas)} quebradas"
        + (f" | {quebradas[:15]}" if quebradas else ""))
    # ------------------------------------------------------------ teste 1
    vazios = {p["n"] for p in modelo["paragrafos"] if not p["texto"].strip()}
    nv = {p["n"] for p in modelo["paragrafos"] if p["texto"].strip()}
    cob = Counter()
    for r in M["M02"]:
        m = re.search(r"parágrafos? (\d+)(?: a (\d+))?", r["fonte"])
        if m and not r["id"].startswith("TR-NE"):
            for i in range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1):
                if i not in vazios:
                    cob[i] += 1
    faltam, duplos = sorted(nv - set(cob)), sorted(i for i in nv if cob[i] > 1)
    reg(not faltam and not duplos, f"teste 1: {len(nv) - len(faltam)} de {len(nv)} parágrafos não vazios do modelo em "
        f"exatamente um bloco do M02 ({100 * (len(nv) - len(faltam)) / len(nv):.2f}%); blocos tirados das notas (TR-NE*) "
        f"fora da conta: {sum(1 for r in M['M02'] if r['id'].startswith('TR-NE'))}")
    # ------------------------------------------------------------ teste 2
    ne = M["M03"]
    sem = [r["id"] for r in ne if r["bloco_ancora"] not in ordem02]
    reg(sorted(r["id"] for r in ne) == [f"NE-{k:03d}" for k in range(1, 103)] and not sem,
        f"teste 2: {len(ne)} notas (NE-001 a NE-102) ligadas a bloco existente do M02" + (f" | sem bloco {sem}" if sem else ""))
    # ------------------------------------------------------------ teste 4
    chaves07 = {r["chave"] for r in M["M07"]}
    faltando = []
    for k in ARQS:
        if k in ("M07",):
            continue
        for r in M[k]:
            for col, val in r.items():
                if col in ("status", "validacao", "comentario_validacao", "condicao_expr", "liga_expr", "desliga_expr") or not val:
                    continue
                cits = [c.strip() for c in val.split(";")] if col in ("normas", "citacoes") else extrair(val)
                for c in cits:
                    if not c or re.match(r"^Lei\d", c):
                        continue
                    for i in identidades(c):
                        if i[0] not in chaves07:
                            faltando.append(f"{k}:{r.get(CHAVE.get(k, 'id'))}.{col} -> {i[1]}")
    reg(not faltando, f"teste 4: normas citadas de M00 a M11 presentes no M07 ({len(chaves07)} normas): "
        f"{len(faltando)} faltando" + (f" | {faltando[:10]}" if faltando else ""))
    sem_base = [r["id"] for r in M["M07"] if r["situacao"] == "NAO_CONFERIDA" and
                not set(r["origem"].split("; ")) & {"MODELO_AGU", "NOTA_AGU", "CORPUS", "CHECKLIST"}]
    reg(not sem_base, f"teste 4: norma citada só em texto das matrizes, sem base nem conferência: {len(sem_base)}")
    av = [r["id"] for r in M["M07"] if r["status"] == "A_VERIFICAR" and r["situacao"] != "NAO_CONFERIDA"]
    reg(not av, "M07: status A_VERIFICAR só em norma não conferida")
    # ------------------------------------------------------------ teste 5
    vaz, fora = [], []
    for k in ARQS:
        for r in M[k]:
            rid = r.get(CHAVE.get(k, "id"))
            if not r.get("fonte", "").strip() or not r.get("status", "").strip():
                vaz.append(f"{k}:{rid}")
            if r.get("status") not in STATUS:
                fora.append(f"{k}:{rid}={r.get('status')}")
    total = sum(len(v) for v in M.values())
    reg(not vaz and not fora, f"teste 5: fonte e status preenchidos e no domínio nas {total} linhas de M00 a M11"
        + (f" | vazios {vaz[:5]} | fora {fora[:5]}" if vaz or fora else ""))
    # ------------------------------------------------------------ teste 6
    obrig = sorted({r["inciso_art18"] for r in M["M01"] if r["obrigatorio_par2"] == "S" and r["inciso_art18"]})
    reg(obrig == sorted(["I", "IV", "VI", "VIII", "XIII"]), f"teste 6: incisos obrigatórios no M01 = {obrig}")
    # ------------------------------------------------------------ teste 7 (resultado do verifica_nomes.py)
    log7 = pasta / "logs" / "f9_nomes.txt"
    if log7.exists():
        t7 = log7.read_text(encoding="utf-8")
        m = re.search(r"achados: (\d+)", t7)
        reg(m is not None and m.group(1) == "0", f"teste 7: nomes de pessoas nos arquivos de saída: "
            f"{m.group(1) if m else 'log sem resultado'} ({t7.splitlines()[0] if t7 else ''})")
    else:
        reg(False, "teste 7: logs/f9_nomes.txt ausente (rodar verifica_nomes.py antes)")
    # ------------------------------------------------------------ teste 8
    cobertos = Counter()
    for k in ("M09", "M10"):
        for r in M[k]:
            for n in re.findall(r"seção 5, achados? (\d+)", r["achado"]):
                cobertos[int(n)] += 1
    falt8 = [n for n in ACHADOS_S5 if not cobertos[n]]
    reg(not falt8, "teste 8: achados da seção 5 (lista reconstruída, 10) no M09 ou no M10: "
        + ", ".join(f"{n}={cobertos[n]}" for n in ACHADOS_S5) + (f" | faltam {falt8}" if falt8 else ""))
    a22 = Counter(n for k in ("M09", "M10") for r in M[k] for n in re.findall(r"anexo 22/10, achado (\d+)", r["achado"]))
    out.append(f"INFO  achados de 22/10/2026 citados no M09 ou no M10: {dict(sorted(a22.items()))} (o 1, nenhum arquivo novo "
               f"é TR, está no M00; o 5, sem DFD do processo PROC-02, está na P10)")
    # ------------------------------------------------------------ domínios
    dom = {"M04": {"documento": {"ETP", "TR", "AMBOS"}, "tipo_resposta": {"SIM_NAO", "UNICA", "MULTIPLA", "NUMERO", "DATA", "TEXTO"},
                   "validacao": {"", "OK", "CORRIGIR", "DUVIDA"}},
           "M03": {"validacao": {"", "OK", "CORRIGIR", "DUVIDA"},
                   "natureza": {"CONDICAO", "OBRIGACAO", "VEDACAO", "ORIENTACAO_REDACAO", "REMISSAO_NORMATIVA",
                                "PROCEDIMENTO_FORA_DO_TR"}},
           "M05": {"tipo_dado": {"TEXTO", "NUMERO", "MOEDA", "DATA", "LISTA", "TABELA"}, "obrigatoria": {"S", "N", "CONDICIONAL"},
                   "origem": {"DFD", "WIZARD", "SISTEMA", "PESQUISA_PRECOS", "CHECKLIST"}},
           "M07": {"situacao": {"VIGENTE", "REVOGADA", "NAO_CONFERIDA"}},
           "M08": {"documento": {"ETP", "TR", "AMBOS"}},
           "M10": {"tipo": {"BLOQUEIO", "ALERTA", "INFORMATIVO"}, "momento": {"CHECKLIST", "ITENS", "WIZARD", "MINUTA", "IMPORTACAO"}},
           "M11": {"tipo_resposta": {"SIM_NAO", "UNICA", "MULTIPLA", "TEXTO", "NUMERO", "TABELA"}, "por_item": {"S", "N"},
                   "efeito": {"PREENCHE", "SUGERE", "JUSTIFICA", "ALERTA", "SO_CONTROLE"}, "checklist": {"CONSUMO", "PERMANENTES", "COMPLEMENTO"}},
           "M06": {"teste_par_117": {"CONSISTENTE", "PARCIAL", "DIVERGENTE", "NAO_LIDO", "NAO_TESTADO"},
                   "teste_caso_67_23": {"CONSISTENTE", "PARCIAL", "DIVERGENTE", "NAO_LIDO", "NAO_TESTADO"}}}
    for k, d in dom.items():
        ruins = [f"{r.get(CHAVE.get(k, 'id'))}.{c}={r.get(c)}" for r in M[k] for c, vals in d.items() if r.get(c) not in vals]
        reg(not ruins, f"{k}: colunas de domínio fechado no domínio" + (f" | {ruins[:8]}" if ruins else ""))
    # ------------------------------------------------------------ M06 e M11
    reg(sorted(ids["M06"]) == sorted(lista02), f"M06: uma linha por bloco do M02 ({len(ids['M06'])} de {len(lista02)})")
    so = [r["id"] for r in M["M11"] if (r["efeito"] == "SO_CONTROLE") != (not r["destinos"])]
    reg(not so, "M11: toda pergunta tem destino ou é SO_CONTROLE com motivo na regra" + (f" | {so}" if so else ""))
    hashes = {}
    for f in sorted((docs / "Checklists").glob("*.docx")):
        hashes[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    ok_hash = all(any(h[:12] in r["fonte"] for r in M["M11"]) for h in hashes.values()) and len(hashes) == 2
    reg(ok_hash, "M11: hash dos dois checklists da base confere com o registrado nas linhas: "
        + "; ".join(f"{n[:40]}... {h[:12]}" for n, h in hashes.items()))
    # ------------------------------------------------------------ JSON Logic e Fase 10 (f10_testes.py)
    from f10_testes import testes as testes_f10
    for ok, msg in testes_f10(pasta, M):
        reg(ok, msg)
    sem_expr = [r["id"] for r in M["M02"] if not r["condicao_expr"]]
    reg(not sem_expr, f"M02: condicao_expr preenchida em todos os blocos ({len(M['M02'])})")
    # ------------------------------------------------------------ evidências literais do M08
    pastas_doc = {"TR 117/2025": "TR_exemplos_Termo_de_Refer_ncia_3_pdf", "TR 190/2025": "TR_exemplos_1e19dfeb_ac58_4ae4_aa3c_8114737d3f86_pdf",
                  "TR 23/2026": "TR_exemplos_ae4297a4_a494_4822_980f_6cbcc6b4571c_pdf",
                  "TR 58/2026": "TR_exemplos_f518d222_2d93_4dd0_8068_55769fe133c5_pdf",
                  "ETP 117/2025": "ETP_exemplos_Estudo_T_cnico_Preliminar_2_pdf",
                  "ETP 99/2025": "ETP_exemplos_d4ef8f94_2e0a_4181_8d58_22ed3bdf305c_pdf",
                  "ETP 19/2026": "ETP_exemplos_39f4f8bb_fab9_4793_bbba_6d8cc9196eab_pdf"}
    nq, ruins = 0, []
    for r in M["M08"]:
        for m in re.finditer(r"(TR|ETP) (\d+/\d{4}) \([^)]*\) p\.(\d+): '(.+?)'(?=;|$| \()", r["evidencia_corpus"]):
            doc = f"{m.group(1)} {m.group(2)}"
            f = texto / pastas_doc[doc] / f"p{int(m.group(3)):03d}.txt"
            pag = re.sub(r"\s+", " ", f.read_text(encoding="utf-8")) if f.exists() else ""
            nq += 1
            if re.sub(r"\s+", " ", m.group(4)) not in pag:
                ruins.append(f"{r['id']} {doc} p.{m.group(3)}")
    reg(not ruins and nq > 0, f"M08: {nq} trechos de evidência conferidos letra a letra no texto do corpus" + (f" | {ruins}" if ruins else ""))
    # ------------------------------------------------------------ travessão
    trav = []
    for k in ARQS:
        for r in M[k]:
            for col, val in r.items():
                if col not in LITERAIS and "—" in val:
                    trav.append(f"{k}:{r.get(CHAVE.get(k, 'id'))}.{col}")
    for md in ("README.md", "perguntas_abertas.md", "sugestoes_checklist.md", "auditoria_matrizes_01_02.md"):
        if (pasta / md).exists():
            linhas_md = [i for i, l in enumerate((pasta / md).read_text(encoding="utf-8").splitlines(), 1)
                         if "—" in l and "Matriz Campo a Campo" not in l]
            trav += [f"{md}:{i}" for i in linhas_md]
    reg(not trav, f"travessão (U+2014) fora das colunas literais e nos .md: {len(trav)}" + (f" | {trav[:8]}" if trav else ""))
    # ------------------------------------------------------------ simulação e controle negativo
    sim = (pasta / "logs" / "f6_simulacao_wizard.txt").read_text(encoding="utf-8")
    cen = len(re.findall(r"^== ", sim, flags=re.M))
    reg("TOTAL DE PROBLEMAS: 0" in sim, f"simulação do wizard: {cen} cenários, {sim.strip().splitlines()[-1]}")
    tmp = Path(tempfile.mkdtemp())
    for v in ("M02_tr_blocos.csv", "M04_wizard.csv", "M08_clausulas_setoriais.csv", "M10_validacoes.csv"):
        shutil.copy(pasta / v, tmp / v)

    def regrava(nome, mudar):
        rows = ler(tmp / nome)
        for r in rows:
            mudar(r)
        with open(tmp / nome, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(rows)
    regrava("M02_tr_blocos.csv", lambda r: r.update(condicao_expr="true") if r["id"] == "TR-1.3" else None)
    regrava("M04_wizard.csv", lambda r: r.update(liga_expr=r["liga_expr"].replace('"SIM"', '"NAO"', 1)) if r["id"] == "WZ-23" else None)
    regrava("M08_clausulas_setoriais.csv",
            lambda r: r.update(condicao_expr='{"==":[{"var":"CK_C_10_1"},"Sim"]}') if r["id"] == "SET-01" else None)
    res = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve().parent / "f3_simular_wizard.py"),
                          str(tmp / "M02_tr_blocos.csv"), str(tmp / "M04_wizard.csv"), str(tmp / "saida.txt")],
                         capture_output=True, text=True)
    tipos = {("TR-1.3" in l, "WZ" in l or "liga_expr" in l, "SET-01" in l) for l in res.stdout.splitlines() if "PROBLEMA" in l}
    det = (any(t[0] for t in tipos), any("liga_expr" in l for l in res.stdout.splitlines()),
           any("SET-01" in l for l in res.stdout.splitlines()))
    shutil.rmtree(tmp)
    reg(all(det), f"controle negativo da simulação: 3 erros injetados (condição de bloco, liga_expr, cláusula setorial), "
        f"detectados {sum(det)}")
    # ------------------------------------------------------------ resumo
    for k in ARQS:
        out.append(f"INFO  {k}: {len(M[k])} linhas | status {dict(Counter(r['status'] for r in M[k]))}")
    out.append(f"FALHAS: {falhas}")
    saida.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
