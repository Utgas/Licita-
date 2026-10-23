#!/usr/bin/env python3
"""M12: valores numéricos e limites usados pelas regras em JSON Logic (Fase 10, tarefa 4).

Nenhuma expressão das matrizes traz número de lei ou valor monetário: o valor vem de `parametros.<nome>`, e cada nome
tem uma linha aqui. O motor lê o M12 e entrega os valores em `parametros` (também dentro de cada item, ver README).

Uso como módulo: PARAMETROS (lista de linhas) e VALORES (nome -> valor tipado, para o simulador).
Uso como script: python3 -I parametros.py <pasta_Matrizes_v1>  (grava M12_parametros.csv; usado_em é preenchido
procurando `parametros.<nome>` em todas as colunas *_expr das matrizes).
"""
import csv
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv  # noqa: E402

COLS = ["id", "nome", "valor", "tipo", "unidade", "base", "vigencia", "usado_em", "fonte", "status"]
DEC8538 = ("Decreto 8.538/2015 conferido em https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/decreto/d8538.htm "
           "em 22/10/2026 (M07, NRM-027)")
LC123 = ("LC 123/2006, art. 48, conferida como vigente em https://planalto.gov.br/ccivil_03/leis/LCP/Lcp123.htm em "
         "23/10/2026; a página carregada termina antes do art. 48, cuja redação foi localizada só no repositório auxiliar "
         "(M07, NRM-050)")

# (nome, valor, tipo, unidade, base, vigencia, fonte, status)
_P = [
    ("limite_exclusivo_me_epp", "80000.00", "numero", "R$ por item ou grupo (valor estimado da unidade de disputa)",
     "LC 123/2006, art. 48, I; Decreto 8.538/2015, art. 6º; NE-003 nota 4", "06/10/2015 (Decreto 8.538/2015)",
     f"Valor literal da NE-003 nota 4 ('até R$ 80.000,00'). {DEC8538}: art. 6º, exclusividade até R$ 80.000,00 por item "
     f"ou lote. {LC123}.", "EXTRAIDO"),
    ("percentual_maximo_cota_me_epp", "25", "numero", "% do objeto de natureza divisível",
     "LC 123/2006, art. 48, III; Decreto 8.538/2015, art. 8º; NE-022", "06/10/2015 (Decreto 8.538/2015)",
     f"Valor literal da NE-022 ('cota de até 25% (vinte e cinco por cento) do objeto'). {DEC8538}: art. 8º, cota de até "
     f"25% em bens divisíveis. Limite da VAR-057 (validacao).", "EXTRAIDO"),
    ("divisor_percentual", "100", "numero", "adimensional",
     "conversão de percentual em fração (quantidade x VAR-057 / 100)", "",
     "Constante aritmética da VAR-160 (cota calculada: parte inteira de quantidade x VAR-057 / 100), da qual dependem a "
     "VAR-113 (tratamento ME/EPP) e a VAR-118 (quantidade da cota); não vem de norma.",
     "INFERIDO"),
    ("garantia_padrao_meses", "12", "numero", "meses",
     "CK-P-13.2 (texto da pergunta: 'garantia superior a 12 meses'); NE-029 nota 2 (justificar a garantia nos autos)",
     "versão do checklist de permanentes mapeada no M11",
     "Valor literal da pergunta 13.2 do checklist de permanentes. A NE-029 não fixa o prazo: só manda justificar.",
     "EXTRAIDO"),
    ("prazo_entrega_referencia", "30", "numero", "dias corridos",
     "CK-C-12.2 (texto da pergunta: 'menor ou maior que 30 dias'); opção '30 dias' da CK-C-12.1",
     "versão do checklist de consumo mapeada no M11",
     "Número da opção '30 dias' da CK-C-12.1, comparado com a VAR-060, que recebe o prazo da 12.1 em número (a pergunta "
     "12.2 é ambígua, DV-28).", "EXTRAIDO"),
    ("quantidade_unitaria", "1", "numero", "unidades do item",
     "CK-C-4.7 ('quantidade igual a uma unidade'); CK-P-4.4 ('quantidade de 1 (uma) unidade')",
     "versão dos checklists mapeada no M11", "Texto das perguntas 4.7 (consumo) e 4.4 (permanentes).", "EXTRAIDO"),
    ("marcador_lei_pregao_revogada", "10.520", "texto", "trecho procurado no texto livre",
     "Lei 10.520/2002, revogada pela Lei 14.133/2021 (M07, NRM-054, conferida no Planalto em 22/10/2026)", "",
     "Marcador da VAL-004.", "EXTRAIDO"),
    ("marcador_lei_pregao_revogada_sem_ponto", "10520", "texto", "trecho procurado no texto livre",
     "Lei 10.520/2002 (M07, NRM-054)", "", "Marcador da VAL-004 (grafia sem ponto).", "EXTRAIDO"),
    ("marcador_lei_licitacoes_anterior", "8.666", "texto", "trecho procurado no texto livre",
     "Lei 8.666/1993, revogada pela Lei 14.133/2021 (M07, NRM-072, conferida no Planalto em 23/10/2026)", "",
     "Marcador da VAL-004.", "EXTRAIDO"),
    ("marcador_decreto_pregao_eletronico_anterior", "10.024", "texto", "trecho procurado no texto livre",
     "Decreto 10.024/2019 (M07, NRM-015, NAO_CONFERIDA)", "", "Marcador da VAL-004; situação do decreto não conferida.",
     "A_VERIFICAR"),
    ("marcador_in_sustentabilidade_anterior", "SLTI/MP", "texto", "trecho procurado no texto livre",
     "IN SLTI/MP 1/2010 (M07, NRM-049, NAO_CONFERIDA)", "", "Marcador da VAL-004; situação da IN não conferida.",
     "A_VERIFICAR"),
    ("classes_tic", "[]", "lista", "classes de material (texto da classe e PDM, como no DFD)",
     "lista mantida pela OM (VAR-154); o sistema não traz lista própria", "",
     "Sem valor na base: a OM cadastra. Lista vazia faz todo item sair com tic = N.", "A_VERIFICAR"),
]


def _tipado(valor, tipo):
    if tipo == "numero":
        return float(valor) if "." in valor else int(valor)
    if tipo == "lista":
        return json.loads(valor)
    return valor


VALORES = {n: _tipado(v, t) for (n, v, t, *_r) in _P}
NOMES = set(VALORES)


def usos(pasta):
    out = {}
    for f in sorted(glob.glob(str(Path(pasta) / "M*.csv"))):
        if Path(f).name.startswith("M12"):
            continue
        rows = list(csv.DictReader(open(f, encoding="utf-8-sig")))
        if not rows:
            continue
        for c in [c for c in rows[0] if c.endswith("_expr")]:
            for r in rows:
                for n in NOMES:
                    if f'"parametros.{n}"' in r[c]:
                        out.setdefault(n, []).append(f"{r['id']}.{c}")
    return out


def main():
    pasta = Path(sys.argv[1])
    u = usos(pasta)
    linhas = []
    extra = {"percentual_maximo_cota_me_epp": ["VAR-057.validacao"]}
    for i, (n, v, t, un, base, vig, fonte, st) in enumerate(_P, 1):
        ondes = u.get(n, []) + extra.get(n, [])
        linhas.append({"id": f"PAR-{i:02d}", "nome": n, "valor": v, "tipo": t, "unidade": un, "base": base, "vigencia": vig,
                       "usado_em": "; ".join(ondes), "fonte": fonte + " Tipo do valor: " + t + ".", "status": st})
    gravar_csv(pasta / "M12_parametros.csv", COLS, linhas, preservar=())
    sem_uso = [l["nome"] for l in linhas if not l["usado_em"]]
    print(f"M12: {len(linhas)} parâmetros; sem uso: {sem_uso}")


if __name__ == "__main__":
    main()
