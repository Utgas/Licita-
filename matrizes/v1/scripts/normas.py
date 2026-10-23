#!/usr/bin/env python3
"""Normalização de citações normativas para o M07 e para o teste 4 da Fase 9 (módulo de análise).

identidades(citacao) devolve a lista de (chave, nome_canonico, tipo, numero, ano, orgao) das normas mencionadas num
trecho de citação, na ordem em que aparecem. Citação sem norma identificável ('art. 182 da mesma Lei',
'art. 6º, inciso XLI, c/c art. 29') devolve lista vazia: quem chama resolve pelo contexto (última norma citada no
mesmo texto). Nada aqui interpreta ou corrige o conteúdo da norma.
"""
import re
import unicodedata

_NUM = r"(?:n[º°.o]*\s*\.?\s*|nº\s*|n\.º\s*|n°\s*|Nº\s*|N\.º\s*)?"
_ANO = r"(?:\s*/\s*(\d{2,4}))?(?:,?\s*(?:de|DE)\s+(?:\d{1,2}º?,?\s*(?:(?:de|DE)\s+)?[A-Za-zçÇ]+\s+(?:(?:de|DE)\s+)?)?(\d{4}))?"
_ORG_IN = r"(SEGES/MGI|SEGES/ME|SEGES/MP|Seges/ME|Seges/MGI|SEGES|DREI/ME|SLTI/MP|SGD/ME|SGD/MGI)"

PADROES = [
    ("LEI_COMPLEMENTAR", re.compile(r"(?:Lei Complementar|LC)\s+" + _NUM + r"(\d[\d.]*)" + _ANO)),
    ("DECRETO_LEI", re.compile(r"Decreto-Lei\s+" + _NUM + r"(\d[\d.]*)" + _ANO)),
    ("MEDIDA_PROVISORIA", re.compile(r"Medida Provisória\s+" + _NUM + r"(\d[\d.]*)" + _ANO)),
    ("DECRETO", re.compile(r"Decreto(?!-Lei)\s+(?:Federal\s+)?" + _NUM + r"(\d[\d.]*)" + _ANO)),
    ("LEI", re.compile(r"(?<![A-Za-z])Lei(?! Complementar| de Usura)\s+" + _NUM + r"(\d[\d.]*)" + _ANO)),
    ("INSTRUCAO_NORMATIVA", re.compile(r"(?:Instrução Normativa|IN)\s+(?:" + _ORG_IN + r"\s+)?" + _NUM + r"(\d+)" + _ANO)),
    ("PORTARIA", re.compile(r"Portaria\s+(Conjunta|SEGES/ME|AGU|INMETRO|SVS/MS|MS)?\s*" + _NUM + r"(\d[\d.]*)" + _ANO)),
    ("RESOLUCAO", re.compile(r"(?:Resolução\s+(?:da Diretoria Colegiada da\s+)?(?:RDC/Anvisa|RDC|CMN|SEGES-CICS/MGI)|RDC)\s*" + _NUM +
                             r"(\d[\d.]*)" + _ANO)),
    ("CIRCULAR", re.compile(r"Circular\s+(?:SUSEP|Susep)\s+" + _NUM + r"(\d+)" + _ANO)),
    ("COMUNICADO", re.compile(r"Comunicado\s+" + _NUM + r"(\d[\d.]*)" + _ANO)),
    ("ORIENTACAO_NORMATIVA", re.compile(r"(?i:orientação normativa)\s+(?:AGU\s+)?" + _NUM + r"(\d+)" + _ANO)),
    ("ACORDAO", re.compile(r"(?:Acórdão|Ac\.)\s*" + _NUM + r"([\d.]+)/(\d{4})(?:\s*[–-]\s*(?:TCU\s*[–-]\s*)?"
                           r"(Plenário|Primeira Câmara|Segunda Câmara))?")),
    ("DECISAO", re.compile(r"Decis(?:ão|ões)\s+([\d.]+)/(\d{4})(?:\s+e\s+([\d.]+)/(\d{4}))?")),
    ("PROCESSO_TCU", re.compile(r"TC-([\d.]+)/(\d{4})-(\d)")),
    ("PARECER", re.compile(r"(?i:parecer)\s+" + _NUM + r"(?:JL\s*[–-]?\s*0?(\d+)(?:/(\d{4}))?|(\d+)/(\d{4})/([A-Z]+(?:/[A-Z]+)*))")),
    ("NOTA", re.compile(r"NOTA\s+n\.\s*(\d+)/(\d{4})/([A-Z]+(?:/[A-Z]+)*)")),
    ("DESPACHO", re.compile(r"(?i:despacho)\s+(?:do\s+(Advogado-Geral da União|Ministro Chefe da Advocacia-Geral da União)\s+)?" + _NUM +
                            r"([\d.]+)(?:/(\d{4})/([A-Z]+(?:/[A-Z]+)*))?(?:,\s*de\s+\d{1,2},?\s+de\s+[a-zç]+\s+de\s+(\d{4}))?")),
    ("CODIGO", re.compile(r"(Código Civil|Código de Defesa do Consumidor|Código Tributário Nacional|Consolidação das Leis do Trabalho|"
                          r"Constituição Federal|Lei de Usura)")),
]

# nomes que o próprio modelo AGU liga a um número (TR-5.5: 'Lei nº 8.078, de 11 de setembro de 1990 (Código de Defesa do
# Consumidor)'); os demais nomes ficam como entradas próprias, sem número que não esteja escrito na base
APELIDO = {"Código de Defesa do Consumidor": ("LEI-8078-1990", "Lei nº 8.078/1990", "LEI", "8078", "1990", "")}

# IN citada sem órgão: órgão tirado de outra citação da mesma IN na base (mesmo número e ano)
ORG_IN_PADRAO = {("58", "2022"): "SEGES/ME", ("77", "2022"): "SEGES/ME", ("81", "2022"): "SEGES/ME",
                 ("73", "2022"): "SEGES/ME", ("98", "2022"): "SEGES/ME", ("65", "2021"): "SEGES/ME",
                 ("116", "2021"): "SEGES/ME", ("26", "2022"): "SEGES/ME", ("82", "2025"): "SEGES/MGI",
                 ("5", "2017"): "SEGES/MP", ("1", "2010"): "SLTI/MP"}


def _ano(a, b=None):
    for x in (b, a):
        if x:
            if len(x) == 2:
                return ("20" if int(x) <= 30 else "19") + x
            return x
    return ""


def _n(x):
    return str(int(x.replace(".", ""))) if x and x.replace(".", "").isdigit() else (x or "")


def identidades(cit):
    achados = []
    usados = []
    for tipo, rx in PADROES:
        for m in rx.finditer(cit):
            if any(m.start() < f and m.end() > i for i, f in usados):
                continue
            g = m.groups()
            ident = None
            if tipo in ("LEI_COMPLEMENTAR", "DECRETO_LEI", "MEDIDA_PROVISORIA", "DECRETO", "LEI", "COMUNICADO"):
                num, ano = _n(g[0]), _ano(g[1], g[2])
                pref = {"LEI_COMPLEMENTAR": "LC", "DECRETO_LEI": "DL", "MEDIDA_PROVISORIA": "MP", "DECRETO": "DEC",
                        "LEI": "LEI", "COMUNICADO": "COMUNICADO"}[tipo]
                nomes = {"LEI_COMPLEMENTAR": "Lei Complementar", "DECRETO_LEI": "Decreto-Lei", "MEDIDA_PROVISORIA":
                         "Medida Provisória", "DECRETO": "Decreto", "LEI": "Lei", "COMUNICADO": "Comunicado"}
                ident = (f"{pref}-{num}-{ano}" if ano else f"{pref}-{num}", f"{nomes[tipo]} nº {g[0]}" + (f"/{ano}" if ano else ""),
                         tipo, num, ano, "")
            elif tipo == "INSTRUCAO_NORMATIVA":
                org, num, ano = g[0], _n(g[1]), _ano(g[2], g[3])
                if org:
                    org = org.upper()
                    if org == "SEGES":
                        org = ORG_IN_PADRAO.get((num, ano), "SEGES/ME")
                else:
                    org = ORG_IN_PADRAO.get((num, ano), "")
                chave = f"IN-{org.replace('/', '-')}-{num}-{ano}" if org else f"IN-{num}-{ano}"
                ident = (chave, f"Instrução Normativa {org} nº {num}/{ano}".replace("  ", " "), tipo, num, ano, org)
            elif tipo == "PORTARIA":
                org, num, ano = (g[0] or "").upper(), _n(g[1]), _ano(g[2], g[3])
                ident = (f"PORTARIA-{org.replace('/', '-')}-{num}-{ano}".replace("--", "-"),
                         (f"Portaria {g[0] or ''} nº {g[1]}" + (f"/{ano}" if ano else "")).replace("  ", " "), tipo, num,
                         ano, org)
            elif tipo == "RESOLUCAO":
                txt = m.group(0)
                org = "ANVISA" if "RDC" in txt else "CMN" if "CMN" in txt else "SEGES-CICS/MGI" if "CICS" in txt else ""
                num, ano = _n(g[0]), _ano(g[1], g[2])
                pref = "RDC-ANVISA" if org == "ANVISA" else f"RESOLUCAO-{org.replace('/', '-')}"
                ident = (f"{pref}-{num}-{ano}" if ano else f"{pref}-{num}",
                         (f"RDC Anvisa nº {num}" if org == "ANVISA" else f"Resolução {org} nº {num}") + (f"/{ano}" if ano else ""),
                         tipo, num, ano, org)
            elif tipo == "CIRCULAR":
                num, ano = _n(g[0]), _ano(g[1], g[2])
                ident = (f"CIRCULAR-SUSEP-{num}-{ano}", f"Circular SUSEP nº {num}/{ano}", tipo, num, ano, "SUSEP")
            elif tipo == "ORIENTACAO_NORMATIVA":
                num, ano = _n(g[0]), _ano(g[1], g[2])
                ident = (f"ON-AGU-{num}-{ano}" if ano else f"ON-AGU-{num}", f"Orientação Normativa AGU nº {num}" +
                         (f"/{ano}" if ano else ""), tipo, num, ano, "AGU")
            elif tipo == "ACORDAO":
                num, ano, col = _n(g[0]), g[1], (g[2] or "")
                c = {"Plenário": "PLENARIO", "Primeira Câmara": "1C", "Segunda Câmara": "2C"}.get(col, "")
                ident = (f"ACORDAO-TCU-{num}-{ano}" + (f"-{c}" if c else ""), f"Acórdão TCU nº {g[0]}/{ano}" +
                         (f"-{col}" if col else ""), tipo, num, ano, "TCU")
            elif tipo == "DECISAO":
                achados.append((m.start(), (f"DECISAO-TCU-{_n(g[0])}-{g[1]}", f"Decisão TCU nº {g[0]}/{g[1]}", tipo, _n(g[0]),
                                            g[1], "TCU")))
                if g[2]:
                    ident = (f"DECISAO-TCU-{_n(g[2])}-{g[3]}", f"Decisão TCU nº {g[2]}/{g[3]}", tipo, _n(g[2]), g[3], "TCU")
            elif tipo == "PROCESSO_TCU":
                ident = (f"TC-{g[0].replace('.', '')}-{g[1]}-{g[2]}", f"Processo TC-{g[0]}/{g[1]}-{g[2]}", tipo, g[0], g[1], "TCU")
            elif tipo == "PARECER":
                if g[0]:
                    ident = ("PARECER-JL-01-2020", "Parecer JL-01/2020", tipo, "JL-01", "2020", "AGU")
                else:
                    ident = (f"PARECER-{g[2]}-{g[3]}-{g[4].replace('/', '-')}", f"Parecer n. {g[2]}/{g[3]}/{g[4]}", tipo,
                             g[2], g[3], g[4])
            elif tipo == "NOTA":
                ident = (f"NOTA-{g[0]}-{g[1]}-{g[2].replace('/', '-')}", f"Nota n. {g[0]}/{g[1]}/{g[2]}", tipo, g[0], g[1], g[2])
            elif tipo == "DESPACHO":
                if g[2]:
                    ident = (f"DESPACHO-{g[1]}-{g[2]}-{g[3].replace('/', '-')}", f"Despacho n. {g[1]}/{g[2]}/{g[3]}", tipo,
                             g[1], g[2], g[3])
                else:
                    ano = g[4] or ""
                    quem = "AGU" if g[0] else ""
                    ident = (f"DESPACHO-{quem}-{_n(g[1])}-{ano}".replace("--", "-"), f"Despacho {g[0] or ''} nº {g[1]}/{ano}"
                             .replace("  ", " "), tipo, _n(g[1]), ano, "AGU")
            elif tipo == "CODIGO":
                nome = g[0]
                sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
                ident = APELIDO.get(nome) or ("COD-" + "-".join(w[:4].upper() for w in sem_acento.split() if len(w) > 2),
                                              nome, "CODIGO", "", "", "")
            if ident:
                achados.append((m.start(), ident))
                usados.append((m.start(), m.end()))
    achados.sort(key=lambda x: x[0])
    vistos, out = set(), []
    for _, ident in achados:
        if ident[0] not in vistos:
            vistos.add(ident[0])
            out.append(ident)
    return out


def dispositivo(cit):
    """Parte da citação antes do nome da norma ('art. 48, II', '§ 1º do art. 4º'), como escrita."""
    m = re.match(r"^(.*?)(?:,?\s+d[aoe]s?\s+|\s*,\s*)(?:mesm[ao]|Lei|Decreto|Instrução|IN\b|LC\b|Código|Constituição|Portaria|"
                 r"Resolução|Circular|Medida|RDC|Anexo)", cit)
    if m and re.search(r"(?i)\b(art|§|inciso|alínea|anexo|caput|parágrafo)", m.group(1)):
        return m.group(1).strip(" ,")
    if re.match(r"(?i)^(art|§|inciso|alínea|caput|parágrafo)", cit) and not identidades(cit):
        return cit.strip(" ,")
    return ""
