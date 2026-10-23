#!/usr/bin/env python3
"""Fase 4 - M06: derivação ETP -> TR, bloco a bloco, com o teste no par ETP 117/2025 x TR 117/2025.

Uso: python3 -I f4_gerar_M06.py <pasta_Matrizes_v1>

Especificação reconstruída (o texto original do prompt não está mais disponível nesta sessão; ver README):
uma linha por bloco do M02, dizendo de onde vem o conteúdo de cada bloco do TR (texto fixo do modelo, campo do ETP,
decisão do wizard, dado do sistema, pesquisa de preços, checklist ou dado do contratado) e qual regra de derivação o
sistema aplica. O caso ETP 67/2026 x TR 23/2026 (mesmo objeto) é o caso de divergência (P08). O par 117/2025 (mesmo
processo no ETP e no TR) é usado como teste: para 14 derivações, o resultado
registra se o TR real repete o ETP real (CONSISTENTE), repete em parte (PARCIAL) ou diverge (DIVERGENTE), com página.
O corpus não prova o que é correto: o teste mostra onde o sistema precisa forçar a coerência entre ETP e TR.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv, ler_csv  # noqa: E402

COLS = ["bloco_tr", "secao", "campos_etp", "variaveis", "perguntas_wz", "classe_origem", "regra_derivacao",
        "teste_par_117", "evidencia_par_117", "teste_caso_67_23", "evidencia_caso_67_23", "fonte", "status"]

ETP117 = "ETP exemplos/Estudo Técnico Preliminar-2.pdf (ETP 117/2025)"
TR117 = "TR exemplos/Termo de Referência-3.pdf (TR 117/2025)"

# resultado do teste no par 117/2025 (leitura por script do texto extraído, conferida na página indicada)
TESTE = {
    "TR-CAB.04": ("CONSISTENTE", "Mesmo número de processo no ETP (p.1) e no TR (p.1)."),
    "TR-1.1": ("PARCIAL", "O TR acrescenta ao objeto 'em regime de consignação com comodato' (p.1); o ETP descreve o objeto "
                          "sem esse regime (p.1) e só trata de consignação e comodato nas definições e na entrega (p.4 a p.7 e p.11)."),
    "TR-1.5": ("CONSISTENTE", "Ata de registro de preços de 12 meses no ETP (p.8) e no TR (p.1)."),
    "TR-9.4": ("DIVERGENTE", "O ETP indica 'menor preço por item' (p.10); o TR adota 'menor preço por grupo ou lote' e justifica "
                             "o não parcelamento (p.5)."),
    "TR-4.H04": ("DIVERGENTE", "O ETP justifica exigência de amostra (8 menções na p.10); o TR não tem nenhuma menção a amostra."),
    "TR-5.4.1": ("CONSISTENTE", "Validade mínima de 50% do prazo de fábrica no ETP (p.2) e 'metade' no TR (p.6)."),
    "TR-10.1": ("CONSISTENTE", "Mesmo valor total estimado no ETP (p.14, campo 'Valor (R$)' e texto) e no TR (p.19)."),
    "TR-9.34": ("DIVERGENTE", "O ETP exige atestado de no mínimo 50% 'pelo período mínimo de 12 meses' (p.15); o TR usa o texto "
                              "genérico de atestados (p.19). A limitação de tempo do ETP contraria a NE-071 (ver M09)."),
    "TR-2.3": ("CONSISTENTE", "O ETP detalha o PCA (p.15) e o TR remete ao ETP (p.3), que é a opção B do grupo GA-03."),
    "TR-5.1": ("DIVERGENTE", "O TR fixa 48 horas e 4 horas na urgência (p.6); o ETP fala em 7 dias antes da cirurgia para material "
                             "com comodato e 48 horas antes da cirurgia para os demais (p.11): termo inicial diferente."),
    "TR-5.4": ("DIVERGENTE", "Endereços de entrega diferentes no ETP (p.11) e no TR (p.6); os endereços não são copiados aqui."),
    "TR-4.1": ("PARCIAL", "O ETP trata de sustentabilidade e cita a IN SLTI/MP 01/2010 (p.16); o TR usa o texto do modelo e "
                          "remete os critérios ao ETP (p.3), sem listá-los nos subitens."),
    "TR-5.5": ("DIVERGENTE", "O TR traz as duas opções do grupo GA-07 (garantia legal e garantia contratual, p.7); o ETP não "
                             "trata de garantia do bem."),
    "TR-1.1.TAB1": ("NAO_LIDO", "No TR a tabela de itens remete a anexo (p.1, item 1.2) que não está no texto extraído; a "
                                "comparação de quantidades por item não foi feita."),
}


ETP67 = "TR exemplos/4bcb2dfc-623c-44fa-a3c1-2ef2e28dbd08.pdf (ETP 67/2026)"
TR23 = "TR exemplos/ae4297a4-a494-4822-980f-6cbcc6b4571c.pdf (TR 23/2026)"
# caso de divergência ETP x TR (P08): mesmo objeto, processos sem vínculo formal no ETP (número em branco)
TESTE_67_23 = {
    "TR-CAB.04": ("DIVERGENTE", "O ETP não tem número de processo (p.1); o TR tem (p.1)."),
    "TR-1.1": ("CONSISTENTE", "Mesmo objeto: ambulância tipo D para o mesmo hospital (ETP p.1; TR p.1)."),
    "TR-1.1.1": ("DIVERGENTE", "O ETP adota registro de preços (p.3, p.4 e p.6); o TR é pregão sem registro de preços, com "
                              "fornecimento integral (p.1)."),
    "TR-10.1": ("DIVERGENTE", "Valores estimados diferentes no ETP (p.4 e p.5) e no TR (p.11)."),
    "TR-5.1": ("PARCIAL", "Mesmo prazo de 120 dias; termo inicial diferente: 'remessa da Nota de Empenho' no ETP (p.3) e "
                          "'recebimento da Nota de Empenho' no TR (p.2)."),
    "TR-1.2": ("DIVERGENTE", "O ETP fundamenta 'bem comum' na Lei 10.520/2002, revogada (p.1); o TR usa o texto do modelo, que "
                            "remete à justificativa do ETP (p.1)."),
}


def tokens_ids(texto, padrao):
    return re.findall(padrao, texto or "")


def classe(origem, formatacao, condicao):
    o = origem.upper()
    cls = []
    for k, rot in (("ETP", "ETP"), ("WIZARD", "WIZARD"), ("SISTEMA", "SISTEMA"), ("PESQUISA_PRECOS", "PESQUISA_PRECOS"),
                   ("CHECKLIST", "CHECKLIST"), ("TABELA DE ITENS", "SISTEMA"), ("CONTRATADO", "CONTRATADO")):
        if k in o and rot not in cls:
            cls.append(rot)
    if o.startswith("MODELO") or not cls:
        cls.insert(0, "MODELO")
    return "; ".join(cls)


def main():
    pasta = Path(sys.argv[1])
    m01 = ler_csv(pasta / "M01_etp_campos.csv")
    m02 = ler_csv(pasta / "M02_tr_blocos.csv")
    m04 = ler_csv(pasta / "M04_wizard.csv")
    m05 = ler_csv(pasta / "M05_variaveis.csv")
    lista = [r["id"] for r in m02]
    ordem = {k: i for i, k in enumerate(lista)}

    def expande(campo):
        ids = set()
        for t in re.findall(r"TR-[A-Za-z0-9.\-]+(?:\.\.TR-[A-Za-z0-9.\-]+)?", campo or ""):
            t = t.rstrip(".-")
            if ".." in t:
                a, b = t.split("..")
                if a in ordem and b in ordem:
                    ids.update(lista[ordem[a]:ordem[b] + 1])
            elif t in ordem:
                ids.add(t)
        return ids

    etp_de = {}
    for r in m01:
        for b in expande(r["destino_tr"]):
            etp_de.setdefault(b, set()).add(r["id"])
    for r in m02:
        for e in tokens_ids(r["origem_dado"], r"ETP-\d{2}\.\d{2}"):
            etp_de.setdefault(r["id"], set()).add(e)
    var_de = {}
    for r in m05:
        for b in expande(r["usada_em"]):
            var_de.setdefault(b, set()).add(r["id"])
    wz_de = {}
    for r in m04:
        for b in expande(r["liga_blocos"]) | expande(r["desliga_blocos"]):
            wz_de.setdefault(b, set()).add(r["id"])

    linhas = []
    for r in m02:
        b = r["id"]
        if r["item_modelo"] == "OU":
            cls, regra = "MODELO", "Separador de opções do modelo: nunca entra na minuta."
        else:
            cls = classe(r["origem_dado"], r["formatacao"], r["condicao_inclusao"])
            partes = []
            if r["formatacao"] == "PRETO":
                partes.append("Copiar o texto do modelo sem alteração (NE-001, item 2)")
            elif r["formatacao"] == "NOTA_EXPLICATIVA":
                partes.append("Texto pronto que está dentro da nota explicativa; copiar literalmente quando a condição valer")
            else:
                partes.append("Texto do modelo com trechos em vermelho preenchidos ou escolhidos (NE-001, item 3)")
            if etp_de.get(b):
                partes.append("o conteúdo repete o que o ETP decidiu em " + ", ".join(sorted(etp_de[b])) +
                              "; o TR não reescreve nem contradiz o ETP: se o dado mudou, o ETP é revisto antes")
            if var_de.get(b):
                partes.append("lacunas preenchidas com " + ", ".join(sorted(var_de[b])))
            if wz_de.get(b):
                partes.append("inclusão ou exclusão decidida por " + ", ".join(sorted(wz_de[b], key=lambda x: int(x[3:]))))
            regra = "; ".join(partes) + "."
        teste, evid = TESTE.get(b, ("NAO_TESTADO", ""))
        t2, e2 = TESTE_67_23.get(b, ("NAO_TESTADO", ""))
        fonte = (f"M02 ({b}: origem_dado, formatacao, condicao_inclusao); M01 destino_tr; M05 usada_em; M04 liga_blocos e "
                 f"desliga_blocos")
        if b in TESTE:
            fonte += f"; teste: {ETP117} e {TR117}, páginas indicadas na evidência"
        if b in TESTE_67_23:
            fonte += f"; caso de divergência: {ETP67} e {TR23}, páginas indicadas na evidência"
        linhas.append({
            "bloco_tr": b, "secao": r["secao"], "campos_etp": "; ".join(sorted(etp_de.get(b, []))),
            "variaveis": "; ".join(sorted(var_de.get(b, []))),
            "perguntas_wz": "; ".join(sorted(wz_de.get(b, []), key=lambda x: int(x[3:]))),
            "classe_origem": cls, "regra_derivacao": regra, "teste_par_117": teste, "evidencia_par_117": evid,
            "teste_caso_67_23": t2, "evidencia_caso_67_23": e2,
            "fonte": fonte, "status": "EXTRAIDO" if (b in TESTE and teste != "NAO_LIDO") or b in TESTE_67_23 else "INFERIDO",
        })
    faltam = sorted((set(TESTE) | set(TESTE_67_23)) - set(lista))
    if faltam:
        raise SystemExit(f"blocos do teste ausentes no M02: {faltam}")
    gravar_csv(pasta / "M06_derivacao_etp_tr.csv", COLS, linhas, preservar=(), chave="bloco_tr")
    from collections import Counter
    print(f"M06: {len(linhas)} linhas; classes: {Counter(l['classe_origem'] for l in linhas).most_common(8)}")
    print("teste par 117:", Counter(l["teste_par_117"] for l in linhas))
    print("caso 67/23:", Counter(l["teste_caso_67_23"] for l in linhas))


if __name__ == "__main__":
    main()
