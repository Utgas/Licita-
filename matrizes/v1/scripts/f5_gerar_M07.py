#!/usr/bin/env python3
"""Fase 5 - M07: normas e orientações citadas nas matrizes, uma linha por norma, com situação conferida quando possível.

Uso: python3 -I f5_gerar_M07.py <pasta_Matrizes_v1> <saida_log.txt>

Especificação reconstruída (ver README). Lê todas as células de M00 a M11 (menos o próprio M07), extrai as citações
(citacoes.extrair) e as normaliza (normas.identidades). Citação sem norma identificável ('art. 182 da mesma Lei') é
atribuída à última norma citada no mesmo texto; se não houver, à última norma citada em outra célula da mesma linha.
A origem de cada citação diz em que nível da hierarquia de fontes ela está:
  MODELO_AGU (texto do modelo, M02), NOTA_AGU (notas explicativas, M03), CORPUS (ETPs, TRs e DFDs citados em M00, M06,
  M08 e M09), CHECKLIST (M11) e MATRIZ (texto escrito nas matrizes, que só pode citar norma da base ou conferida).
situacao: VIGENTE ou REVOGADA só quando conferida em planalto.gov.br, in.gov.br ou gov.br (URL e data na coluna
verificacao); nos demais casos, NAO_CONFERIDA. Norma citada só pelo corpus e não conferida fica A_VERIFICAR.
IDs NRM-xxx são estáveis: a chave de cada norma mantém o ID da geração anterior; norma nova recebe o próximo número.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citacoes import extrair  # noqa: E402
from comum import gravar_csv, ler_csv  # noqa: E402
from normas import dispositivo, identidades  # noqa: E402

COLS = ["id", "chave", "norma", "tipo", "numero", "ano", "orgao", "dispositivos_citados", "formas_citadas", "onde_citada",
        "n_citacoes", "origem", "situacao", "verificacao", "fonte", "status"]

L14133 = "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm"
VERIF = {
    "LEI-14133-2021": ("VIGENTE", f"{L14133}, consultado em 21/10/2026 e 22/10/2026: página sem nota de revogação; art. 18, "
                                  f"§§ 1º e 2º conferidos. A ferramenta de leitura só alcança o texto até o art. 40 (página "
                                  f"de 84.967 caracteres na conversão): artigos posteriores citados nas matrizes vêm do "
                                  f"modelo AGU e das notas, sem conferência própria (P05)."),
    "LEI-10520-2002": ("REVOGADA", "https://planalto.gov.br/ccivil_03/leis/2002/L10520.htm, consultado em 22/10/2026: nota "
                                   "'(Revogado pela Lei nº 14.133, de 2021)' abaixo do título; art. 1º, parágrafo único, "
                                   "conferido."),
    "DEC-8538-2015": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/decreto/d8538.htm, consultado em "
                                "22/10/2026: sem nota de revogação do decreto; arts. 6º (exclusividade até R$ 80.000,00 por "
                                "item ou lote), 8º (cota de até 25% em bens divisíveis; § 4º prioridade da cota em SRP e "
                                "entregas parceladas) e 10 (incisos I a IV) sem nota de alteração. O art. 10, III, ainda remete "
                                "aos arts. 24 e 25 da Lei 8.666/1993."),
    "IN-SEGES-ME-58-2022": ("VIGENTE", "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/"
                                       "instrucoes-normativas/instrucao-normativa-seges-no-58-de-8-de-agosto-de-2022, "
                                       "consultado em 23/10/2026: página sem nota de revogação ou alteração, publicada no "
                                       "DOU de 09/08/2022; art. 9º, caput e § 1º (ao menos os incisos I, V, VI, VII e XIII), "
                                       "e art. 14, I e II, conferidos. A IN consta da lista de INs vigentes do portal "
                                       "(https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/"
                                       "instrucoes-normativas, página 1 de 3). Não está no repositório auxiliar."),
    "IN-SEGES-ME-65-2021": ("VIGENTE", "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/"
                                       "instrucoes-normativas/instrucao-normativa-seges-me-no-65-de-7-de-julho-de-2021, "
                                       "consultado em 23/10/2026: página sem nota de revogação ou alteração, publicada no "
                                       "DOU de 08/07/2021; art. 7º, §§ 4º e 5º, conferidos. Não aparece na página 1 da "
                                       "lista de INs vigentes (páginas 2 e 3 não abertas). Não está no repositório auxiliar."),
    "IN-SEGES-ME-73-2022": ("VIGENTE", "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/"
                                       "instrucoes-normativas/instrucao-normativa-seges-me-no-73-de-30-de-setembro-de-2022, "
                                       "consultado em 23/10/2026: versão '(Comentada - Atualizada)', alterada pela IN "
                                       "SEGES/MGI 79/2024 em vários dispositivos, sem nota de revogação; art. 11, parágrafo "
                                       "único, e art. 29, § 1º, conferidos; página atualizada em 14/10/2024. Consta da lista "
                                       "de INs vigentes do portal. Não está no repositório auxiliar."),
    "IN-SEGES-ME-81-2022": ("VIGENTE", "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/"
                                       "instrucoes-normativas/instrucao-normativa-seges-me-no-81-de-25-de-novembro-de-2022, "
                                       "consultado em 23/10/2026: título marcado '(*)' = republicada por incorreção no DOU de "
                                       "29/11/2022; sem nota de revogação ou alteração; arts. 7º, 8º e 9º, I, III e IV, "
                                       "conferidos. Consta da lista de INs vigentes do portal. Não está no repositório "
                                       "auxiliar."),
    "DEC-12174-2024": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12174.htm, consultado "
                                  "em 23/10/2026: sem nota de revogação; alterado pelo Decreto nº 12.926, de 13/04/2026 "
                                  "(https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12926.htm, DOU de "
                                  "14/04/2026), que deu nova redação ao art. 1º, parágrafo único, ao art. 3º (I, II, b, III, "
                                  "§§ 1º e 2º) e ao art. 5º, § 3º. O art. 2º (cláusulas obrigatórias dos contratos "
                                  "administrativos: I proteção ao trabalho; II trabalho escravo e infantil; III denúncias "
                                  "de discriminação, violência e assédio; IV responsabilidade solidária por subcontratada) "
                                  "não foi alterado. Repositório auxiliar ctresb/leis, commit 15eb09b: "
                                  "federal/decretos/2024/dec-12174-2024-09-11.md tem versao_texto 'original' e não foi usado "
                                  "para o conteúdo. P16."),
    "DEC-12926-2026": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12926.htm, consultado "
                                  "em 23/10/2026: decreto de 13/04/2026 (DOU de 14/04/2026), sem nota de revogação; altera o "
                                  "Decreto 12.174/2024 (art. 1º, parágrafo único; art. 3º; art. 5º, § 3º) e o Decreto "
                                  "9.507/2018. Citado só pela WZ-51 (P16). Repositório auxiliar ctresb/leis, commit 15eb09b: "
                                  "federal/decretos/2026/dec-12926-2026-04-13.md tem versao_texto 'original' e não foi usado."),
    "PARECER-JL-01-2020": ("NAO_CONFERIDA", "http://www.planalto.gov.br/ccivil_03/AGU/Pareceres/2019-2022/PRC-JL-01-2020.htm "
                                            "citado no texto da nota do modelo AGU; página não aberta nesta fase."),
}

# Fase 10, tarefa extra: normas conferidas no Planalto em 23/10/2026, com texto localizado no repositório auxiliar
# ctresb/leis (commit 15eb09b618ff08a38c4dfee06a91bd139d093f5d), só arquivos com versao_texto "compilada (texto vigente)".
# O repositório não é fonte de verdade: a situação vem da página oficial.
COMMIT_LEIS = "15eb09b"


def _repo(caminho, achado):
    return (f" Texto localizado no repositório auxiliar ctresb/leis, commit {COMMIT_LEIS}, arquivo {caminho} "
            f"(versao_texto 'compilada (texto vigente)'): {achado}")


_SEM_REV = "consultado em 23/10/2026: sem nota de revogação da norma como um todo"
_CORTE = " A página oficial carregada pela ferramenta termina antes do dispositivo citado; a redação dele não foi conferida na fonte oficial."
VERIF_REPO = {
    "LC-123-2006": ("VIGENTE", "https://planalto.gov.br/ccivil_03/leis/LCP/Lcp123.htm, " + _SEM_REV + "." + _CORTE
                    + _repo("federal/leis-complementares/2006/lcp-123-2006-12-14.md",
                            "art. 48, caput e incisos I a III, com redação dada pela LC 147/2014.")),
    "LC-73-1993": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp73.htm, " + _SEM_REV
                   + "; art. 40, caput e § 1º, e art. 41 conferidos, sem nota de redação."
                   + _repo("federal/leis-complementares/1993/lcp-73-1993-02-10.md", "arts. 40 e 41.")),
    "LEI-10406-2002": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm, " + _SEM_REV
                       + "; art. 44, VI, marcado '(Revogado pela Lei nº 14.382, de 2022)'." + _CORTE
                       + _repo("federal/leis-ordinarias/2002/lei-10406-2002-01-10.md",
                               "arts. 412 e 827 localizados; art. 44, VI, revogado; Título I-A do Livro II da Parte "
                               "Especial presente como cabeçalho. A nota AGU cita o inciso VI justamente como revogado "
                               "(EIRELI tratada como SLU).")),
    "LEI-5172-1966": ("VIGENTE", "https://planalto.gov.br/ccivil_03/leis/l5172compilado.htm, " + _SEM_REV + "." + _CORTE
                      + _repo("federal/leis-ordinarias/1966/lei-5172-1966-10-25.md", "art. 193 localizado.")),
    "DL-5452-1943": ("VIGENTE", "https://planalto.gov.br/ccivil_03/decreto-lei/Del5452compilado.htm, " + _SEM_REV
                     + " (CLT; notas de vigência e 'Vide' no cabeçalho)."
                     + _repo("federal/decretos-lei/1943/del-5452-1943-05-01.md", "sem dispositivo citado.")),
    "LEI-8078-1990": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm, " + _SEM_REV
                      + "; alteração mais recente indicada: MP nº 1.393, de 2026 (art. 57)."
                      + _repo("federal/leis-ordinarias/1990/lei-8078-1990-09-11.md", "sem dispositivo citado.")),
    "LEI-12305-2010": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2010/lei/l12305.htm, " + _SEM_REV
                       + "; art. 3º, caput, e art. 7º, XI ('prioridade, nas aquisições e contratações "
                       "governamentais, para:'), conferidos."
                       + _repo("federal/leis-ordinarias/2010/lei-12305-2010-08-02.md", "arts. 3º e 7º.")),
    "LEI-10522-2002": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/2002/l10522compilado.htm, " + _SEM_REV
                       + "; art. 6º-A conferido, '(Incluído pela Lei nº 14.973, de 2024)'."
                       + _repo("federal/leis-ordinarias/2002/lei-10522-2002-07-19.md", "art. 6º-A.")),
    "LEI-6360-1976": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/l6360.htm, " + _SEM_REV
                      + "; alteração mais recente indicada: Lei nº 15.440, de 2026 (art. 18)."
                      + _repo("federal/leis-ordinarias/1976/lei-6360-1976-09-23.md", "sem dispositivo citado.")),
    "LEI-8429-1992": ("VIGENTE", "https://planalto.gov.br/ccivil_03/leis/L8429.htm, " + _SEM_REV
                      + "; art. 12, caput, conferido, '(Redação dada pela Lei nº 14.230, de 2021)'."
                      + _repo("federal/leis-ordinarias/1992/lei-8429-1992-06-02.md", "art. 12.")),
    "LEI-12846-2013": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/lei/l12846.htm, " + _SEM_REV
                       + "; art. 5º, caput, conferido."
                       + _repo("federal/leis-ordinarias/2013/lei-12846-2013-08-01.md", "art. 5º.")),
    "LEI-13709-2018": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm, "
                       + _SEM_REV + "; só revogações parciais."
                       + _repo("federal/leis-ordinarias/2018/lei-13709-2018-08-14.md", "sem dispositivo citado.")),
    "LEI-4320-1964": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/l4320.htm, " + _SEM_REV + "."
                      + _repo("federal/leis-ordinarias/1964/lei-4320-1964-03-17.md", "sem dispositivo citado.")),
    "LEI-5764-1971": ("VIGENTE", "https://planalto.gov.br/ccivil_03/leis/l5764.htm, " + _SEM_REV
                      + "; art. 107 conferido, sem nota."
                      + _repo("federal/leis-ordinarias/1971/lei-5764-1971-12-16.md", "art. 107.")),
    "LEI-7116-1983": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/1980-1988/l7116.htm, " + _SEM_REV
                      + "; alterada pelas Leis 12.687/2012, 14.129/2021 e 14.534/2023."
                      + _repo("federal/leis-ordinarias/1983/lei-7116-1983-08-29.md", "sem dispositivo citado.")),
    "LEI-9430-1996": ("VIGENTE", "https://planalto.gov.br/ccivil_03/leis/l9430.htm, " + _SEM_REV + "; só revogações parciais."
                      + _repo("federal/leis-ordinarias/1996/lei-9430-1996-12-27.md", "sem dispositivo citado.")),
    "LEI-9454-1997": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/leis/l9454.htm, " + _SEM_REV
                      + "; art. 3º, § 3º, e art. 6º revogados pela Lei 12.058/2009; §§ 2º e 3º do art. 1º incluídos "
                      "pela Lei 14.534/2023."
                      + _repo("federal/leis-ordinarias/1997/lei-9454-1997-04-07.md", "sem dispositivo citado.")),
    "LEI-12527-2011": ("VIGENTE", "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12527.htm, " + _SEM_REV + "."
                       + _repo("federal/leis-ordinarias/2011/lei-12527-2011-11-18.md", "sem dispositivo citado.")),
    "LEI-8666-1993": ("REVOGADA", "https://www.planalto.gov.br/ccivil_03/leis/l8666cons.htm, consultado em 23/10/2026: "
                      "nota 'Revogado pela Lei nº 14.133, de 2021'. O art. 6º dessa lei termina no inciso XX: as "
                      "citações 'art. 6º, inciso XLI, c/c art. 29' e 'art. 6º, inciso XXXVIII, c/c o art. 29' da nota "
                      "AGU são dispositivos da Lei 14.133/2021 atribuídos à 8.666 pela extração."
                      + _repo("federal/leis-ordinarias/1993/lei-8666-1993-06-21.md",
                              "nota de revogação e art. 6º com incisos até XX.")),
}
# nomes por extenso apontam para a mesma norma
for _alias, _k in (("COD-CODI-CIVI", "LEI-10406-2002"), ("COD-CODI-TRIB-NACI", "LEI-5172-1966"),
                   ("COD-CONS-DAS-LEIS-TRAB", "DL-5452-1943")):
    VERIF_REPO[_alias] = (VERIF_REPO[_k][0], VERIF_REPO[_k][1] + f" Mesma norma que {_k}.")
assert not set(VERIF_REPO) & set(VERIF)
VERIF.update(VERIF_REPO)


# norma citada em texto das matrizes porque reproduz texto fixo dos sistemas presente no corpus
CORPUS_EXTRA = {"DEC-10543-2020": "texto fixo das assinaturas eletrônicas do ETP Digital, do TR Digital e do DFD do "
                                  "Compras.gov, presente em 16 documentos do corpus"}


def origem_de(matriz, coluna):
    if matriz == "M02" and coluna in ("texto_literal", "normas", "lacunas"):
        return "MODELO_AGU"
    if matriz == "M03" and coluna in ("texto_integral", "citacoes", "trecho_ancorado"):
        return "NOTA_AGU"
    if matriz == "M00" or (matriz == "M06" and coluna == "evidencia_par_117") or \
            (matriz == "M08" and coluna in ("evidencia_corpus", "observacao")) or (matriz == "M09" and coluna in ("descricao", "documento")):
        return "CORPUS"
    if matriz == "M11" and coluna in ("pergunta", "opcoes", "orientacao"):
        return "CHECKLIST"
    return "MATRIZ"


def main():
    pasta = Path(sys.argv[1])
    antigos = {r["chave"]: r["id"] for r in ler_csv(pasta / "M07_normas.csv")}
    normas = {}
    nao_resolvidas = []
    arquivos = sorted(p for p in pasta.glob("M*.csv") if not p.name.startswith("M07"))
    for arq in arquivos:
        mat = arq.name[:3]
        rows = ler_csv(arq)
        if not rows:
            continue
        chave_id = list(rows[0].keys())[0]
        for r in rows:
            rid = r[chave_id]
            ultima_linha = None
            for col, txt in r.items():
                if col in ("status", "validacao", "comentario_validacao", "condicao_expr", "liga_expr", "desliga_expr") or not txt:
                    continue
                if col == "fonte":
                    # a coluna fonte cita normas como fonte da própria linha: também entra
                    pass
                cits = [c.strip() for c in txt.split(";")] if col in ("normas", "citacoes") else extrair(txt)
                ultima = None
                for c in cits:
                    if not c or re.match(r"^Lei\d", c):  # nome de arquivo (ex.: 'Lei14133.md'), não citação
                        continue
                    ids = identidades(c)
                    if not ids:
                        alvo = ultima or ultima_linha
                        if not alvo:
                            nao_resolvidas.append(f"{mat} {rid} {col}: {c}")
                            continue
                        ids = [alvo]
                    for ident in ids:
                        k = ident[0]
                        n = normas.setdefault(k, {"ident": ident, "disp": [], "formas": [], "onde": [], "n": 0,
                                                  "origens": set()})
                        n["n"] += 1
                        d = dispositivo(c)
                        if d and d not in n["disp"]:
                            n["disp"].append(d)
                        if c not in n["formas"]:
                            n["formas"].append(c)
                        if rid not in n["onde"]:
                            n["onde"].append(rid)
                        n["origens"].add(origem_de(mat, col))
                    ultima = ids[-1]
                    ultima_linha = ids[-1]
    # IDs estáveis
    prox = max([int(v[4:]) for v in antigos.values()] + [0]) + 1
    linhas = []
    ordem = sorted(normas, key=lambda k: (k not in antigos, int(antigos[k][4:]) if k in antigos else 0, k))
    for k in ordem:
        n = normas[k]
        if k in antigos:
            nid = antigos[k]
        else:
            nid = f"NRM-{prox:03d}"
            prox += 1
        chave, nome, tipo, num, ano, org = n["ident"]
        if k in CORPUS_EXTRA:
            n["origens"].add("CORPUS")
        sit, ver = VERIF.get(k, ("NAO_CONFERIDA", ""))
        origens = sorted(n["origens"])
        na_base = bool(set(origens) & {"MODELO_AGU", "NOTA_AGU"})
        if sit in ("VIGENTE", "REVOGADA") or na_base:
            status = "EXTRAIDO"
        else:
            status = "A_VERIFICAR"
        fonte = (f"Citações extraídas por script das matrizes (onde_citada); origem: {', '.join(origens)}. "
                 f"{'Citada no modelo AGU ou nas notas (fonte de nível 2).' if na_base else 'Não citada no modelo AGU nem nas notas.'}")
        if k in CORPUS_EXTRA:
            fonte += f" Também no corpus: {CORPUS_EXTRA[k]}."
        if sit == "NAO_CONFERIDA" and not ver:
            ver = "Não conferida em fonte oficial nesta fase."
        onde = n["onde"]
        linhas.append({"id": nid, "chave": chave, "norma": nome, "tipo": tipo, "numero": num, "ano": ano, "orgao": org,
                       "dispositivos_citados": "; ".join(n["disp"][:40]) + (" ..." if len(n["disp"]) > 40 else ""),
                       "formas_citadas": " | ".join(n["formas"][:8]) + (f" | ... (+{len(n['formas']) - 8})" if len(n["formas"]) > 8 else ""),
                       "onde_citada": "; ".join(onde[:60]) + (f" ... (+{len(onde) - 60})" if len(onde) > 60 else ""),
                       "n_citacoes": str(n["n"]), "origem": "; ".join(origens), "situacao": sit, "verificacao": ver,
                       "fonte": fonte, "status": status})
    linhas.sort(key=lambda x: int(x["id"][4:]))
    gravar_csv(pasta / "M07_normas.csv", COLS, linhas, preservar=())
    so_matriz = [l for l in linhas if l["origem"] == "MATRIZ" and l["situacao"] == "NAO_CONFERIDA"]
    log = [f"M07: {len(linhas)} normas; citações não resolvidas: {len(nao_resolvidas)}",
           f"origem só MATRIZ e não conferida (deveria ser zero): {[(l['id'], l['norma']) for l in so_matriz]}",
           f"situação: { {s: sum(1 for l in linhas if l['situacao'] == s) for s in ('VIGENTE', 'REVOGADA', 'NAO_CONFERIDA')} }",
           f"status: { {s: sum(1 for l in linhas if l['status'] == s) for s in ('EXTRAIDO', 'INFERIDO', 'A_VERIFICAR')} }"]
    log += [f"NÃO RESOLVIDA: {x}" for x in nao_resolvidas]
    Path(sys.argv[2]).write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log[:6]))
    if len(log) > 4:
        print("\n".join(log[4:14]))


if __name__ == "__main__":
    main()
