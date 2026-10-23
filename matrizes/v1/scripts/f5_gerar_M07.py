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
    "IN-SEGES-ME-58-2022": ("NAO_CONFERIDA", "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/"
                                             "instrucoes-normativas/instrucao-normativa-seges-no-58-de-8-de-agosto-de-2022, "
                                             "consultado em 21/10/2026: a ferramenta devolve resumo, sem texto literal; "
                                             "conteúdo dos arts. 8º, 9º e 14 conferido pelo resumo; situação não declarada "
                                             "na página."),
    "DEC-12174-2024": ("NAO_CONFERIDA", "https://www.gov.br/compras/pt-br/nllc/legislacao-14-133-por-tema/"
                                        "politicas-publicas-licitacoes/garantias-trabalhistas-para-terceirizados, consultado "
                                        "em 22/10/2026: o decreto 'dispõe sobre as garantias trabalhistas a serem observadas "
                                        "na execução dos contratos administrativos'; a página só dá exemplos de serviços com "
                                        "dedicação de mão de obra e não diz se alcança compras. O texto do decreto no "
                                        "planalto.gov.br não pôde ser aberto pela ferramenta (fora da lista de acesso). P16."),
    "PARECER-JL-01-2020": ("NAO_CONFERIDA", "http://www.planalto.gov.br/ccivil_03/AGU/Pareceres/2019-2022/PRC-JL-01-2020.htm "
                                            "citado no texto da nota do modelo AGU; página não aberta nesta fase."),
}


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
