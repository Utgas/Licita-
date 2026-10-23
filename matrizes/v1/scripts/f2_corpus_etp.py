#!/usr/bin/env python3
"""Fase 2 - Situacao de cada secao do ETP Digital nos ETPs do corpus (estatistica do M01).

Uso: python3 -I f2_corpus_etp.py <pasta_texto> <saida.json>

Para cada ETP do corpus, divide o texto pelas secoes do ETP Digital, reconhecidas pelo NOME (P06:
o numero impresso e posicional) e classifica cada secao em:
  PREENCHIDO    texto proprio na secao;
  REMISSAO      a secao so remete a outro documento (ex.: ao orgao gerenciador da IRP);
  NAO_SE_APLICA a secao declara que nao se aplica;
  OMITIDO       o titulo da secao nao aparece num documento lido por inteiro;
  NAO_LIDO      a secao cairia em pagina ausente do arquivo (ETP 19/2026, P04).
Campos com dado proprio (numero do processo, valor) sao classificados a parte.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ETPS = {  # prefixo da pasta de texto -> rotulo
    "ETP_exemplos_39f4f8bb": "ETP 19/2026",
    "ETP_exemplos_Estudo_T_cnico_Preliminar_2": "ETP 117/2025",
    "ETP_exemplos_Outro_ETP160322_000058_2025": "ETP 58/2025",
    "ETP_exemplos_d4ef8f94": "ETP 99/2025",
    "ETP_exemplos_ed187742": "ETP 151/2025",
    "ETP_exemplos_fdace9da": "ETP 330/2025",
    "TR_exemplos_08955b4e": "ETP 801/2025",
    "TR_exemplos_4bcb2dfc": "ETP 67/2026",
    "ETP_exemplos_882d42e8": "ETP 109/2024",
}
SECOES = [  # codigo estavel, nome de referencia, padrao do titulo
    ("01", "Informações Básicas", r"Informações Básicas"),
    ("02", "Descrição da necessidade", r"Descrição da necessidade"),
    ("03", "Área requisitante", r"Área requisitante"),
    ("04", "Descrição dos Requisitos da Contratação", r"Descrição dos Requisitos da Contratação"),
    ("05", "Levantamento de Mercado", r"Levantamento de Mercado"),
    ("06", "Descrição da solução como um todo", r"Descrição da solução como um todo"),
    ("07", "Estimativa das Quantidades a serem Contratadas", r"Estimativa das Quantidades a serem Contratadas"),
    ("08", "Estimativa do Valor da Contratação", r"Estimativa do Valor da Contratação"),
    ("09", "Justificativa para o Parcelamento ou não da Solução", r"Justificativa para o Parcelamento ou não da Solução"),
    ("10", "Contratações Correlatas e/ou Interdependentes", r"Contratações Correlatas e/ou Interdependentes"),
    ("11", "Alinhamento entre a Contratação e o Planejamento", r"Alinhamento entre a Contratação e o Planejamento"),
    ("12", "Resultados Pretendidos", r"(?:Resultados Pretendidos|Benefícios a serem alcançados com a contratação)"),
    ("13", "Providências a serem Adotadas", r"Providências a serem Adotadas"),
    ("14", "Possíveis Impactos Ambientais", r"Possíveis Impactos Ambientais"),
    ("15", "Declaração de Viabilidade", r"Declaração de Viabilidade"),
    ("16", "Responsáveis", r"Responsáveis"),
    ("90", "Seção adicional (Justificativas pontuais)", r"Justificativas pontuais"),
]
LIXO = re.compile(r"^\s*(UASG \d+.*|.*Estudo Técnico Preliminar \d+/\d{4}.*|\d+\s?de\s?\d+|=+ PAGINA.*|\[--- OCR ---\]|"
                  r"(?:POLICLINICA|HOSPITAL|BASE ADMINISTRATIVA).*)\s*$", re.I)
REMISSAO = re.compile(r"(a cargo d[ao] (?:unidade|órgão) gerenciador|d[oa] (?:órgão|unidade) gerenciador|"
                      r"pel[ao] (?:unidade|órgão) gerenciador|Termo de Referência referente a IRP|órgão de origem da Ata)", re.I)
NA = re.compile(r"\bn[ãa]o se aplica\b", re.I)
NEG = re.compile(r"^(?:\d+(?:\.\d+)*\.?\s*)*(?:Após análise, |Deve-se considerar:\s*)?n[ãa]o (?:há|foram identificad|existe|se faz necess|haverá)", re.I)


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def paginas_doc(d):
    return sorted(d.glob("p[0-9][0-9][0-9].txt"))


def main():
    base = Path(sys.argv[1])
    saida = {}
    for pref, rot in ETPS.items():
        d = next(p for p in base.iterdir() if p.is_dir() and p.name.startswith(pref))
        linhas = []
        for f in paginas_doc(d):
            pg = int(f.stem[1:])
            for l in f.read_text(encoding="utf-8").splitlines():
                linhas.append((pg, l))
        # localiza titulos (linha "N. Titulo")
        marcas = []
        for i, (pg, l) in enumerate(linhas):
            for cod, nome, pat in SECOES:
                if re.match(rf"^\s{{0,4}}\d{{1,2}}\.\s+{pat}\s*$", l, flags=re.I):
                    marcas.append((i, cod, pg, int(re.match(r"\s*(\d+)", l).group(1))))
        marcas.sort()
        res = {}
        for k, (i, cod, pg, num) in enumerate(marcas):
            fim = marcas[k + 1][0] if k + 1 < len(marcas) else len(linhas)
            corpo = [l for _, l in linhas[i + 1:fim] if l.strip() and not LIXO.match(l)]
            txt = re.sub(r"\s+", " ", " ".join(corpo)).strip()
            if cod == "15":
                txt_proprio = re.sub(r"Esta equipe de planejamento declara viável esta contratação\.?", "", txt).strip()
                txt_proprio = re.sub(r"^15\.1\.?\s*Justificativa da Viabilidade", "", txt_proprio).strip()
            elif cod == "16":
                txt_proprio = re.sub(r"Todas as assinaturas eletrônicas seguem.*?2020\.", "", txt).strip()
            else:
                txt_proprio = txt
            if cod == "01":
                m = re.search(r"Número do processo:\s*([\d./-]+)", txt)
                situ = "PREENCHIDO" if m else "EM_BRANCO"
                det = m.group(1) if m else ""
            elif not txt_proprio:
                situ, det = "VAZIO", ""
            elif NA.search(txt_proprio) and len(txt_proprio) < 300:
                situ, det = "NAO_SE_APLICA", txt_proprio[:120]
            elif REMISSAO.search(txt_proprio) and len(txt_proprio) < 420:
                situ, det = "REMISSAO", txt_proprio[:160]
            else:
                situ, det = "PREENCHIDO", txt_proprio[:80]
            negativa = bool(situ == "PREENCHIDO" and NEG.search(txt_proprio))
            res[cod] = {"situacao": situ, "pagina": pg, "numero_impresso": num, "chars": len(txt_proprio),
                        "inicio": det, "declara_inexistencia": negativa if cod != "01" else False}
        # secoes ausentes
        for cod, nome, _ in SECOES:
            if cod in res:
                continue
            if rot == "ETP 19/2026" and cod != "90":
                res[cod] = {"situacao": "NAO_LIDO", "pagina": None, "numero_impresso": None, "chars": 0,
                            "inicio": "título em página ausente do arquivo (P04)"}
            elif cod != "90":
                res[cod] = {"situacao": "OMITIDO", "pagina": None, "numero_impresso": None, "chars": 0, "inicio": ""}
        # caso particular: ETP 19/2026, secao 15 tem o subitem 15.1 na p.5 mesmo sem o titulo
        if rot == "ETP 19/2026" and res.get("15", {}).get("situacao") == "NAO_LIDO":
            t5 = (d / "p005.txt").read_text(encoding="utf-8")
            if re.search(r"15\.1\.?\s*Justificativa da Viabilidade", t5):
                res["15"] = {"situacao": "PREENCHIDO", "pagina": 5, "numero_impresso": None, "chars": 0,
                             "inicio": "título em página ausente; subitem 15.1 lido na p.5"}
        # campo Valor (R$) da secao 8
        txt_all = " ".join(l for _, l in linhas)
        mv = re.search(r"Valor \(R\$\):\s*([\d.,]+)", txt_all)
        saida[rot] = {"pasta": d.name, "secoes": res, "valor_campo": mv.group(1) if mv else None}
    # resumo por secao
    resumo = {}
    for cod, nome, _ in SECOES:
        cont = {}
        for rot, v in saida.items():
            x = v["secoes"].get(cod, {})
            s = x.get("situacao")
            if s:
                cont[s] = cont.get(s, 0) + 1
                if x.get("declara_inexistencia"):
                    cont["PREENCHIDO_COM_DECLARACAO_DE_INEXISTENCIA"] = cont.get("PREENCHIDO_COM_DECLARACAO_DE_INEXISTENCIA", 0) + 1
        resumo[cod] = cont
    json.dump({"etps": saida, "resumo": resumo}, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for cod, nome, _ in SECOES:
        print(cod, nome[:45].ljust(45), resumo[cod])
    for rot, v in saida.items():
        print(rot, {k: x["situacao"][:4] + (f"@{x['numero_impresso']}" if x["numero_impresso"] else "") for k, x in sorted(v["secoes"].items())},
              "valor:", v["valor_campo"])


if __name__ == "__main__":
    main()
