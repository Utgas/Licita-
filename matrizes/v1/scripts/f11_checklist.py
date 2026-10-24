#!/usr/bin/env python3
"""Fase 11 - o checklist distribuído não muda (decisão 0009): leitura, revisão e complementos do operador no M11.

Uso: python3 -I f11_checklist.py <pasta_Matrizes_v1> <saida_log.txt>

Roda depois do f10_gerar_expr.py. Acrescenta ao M11:
  leitura           como ler a resposta do Word e qual prevalece em duplicidade (texto);
  revisao_expr      JSON Logic; verdadeira = a resposta fica destacada para o operador revisar (só operadores gerais);
  revisao_pergunta  pergunta que o sistema faz ao operador quando a dúvida muda a minuta (vazia quando basta o destaque);
  revisao_motivos   (Fase 14) JSON: uma entrada por motivo {motivo, expr, texto, bloqueia}; motivos fixos SEM_RESPOSTA,
                    MARCAS_MULTIPLAS, OUTRO_ILEGIVEL, DIVERGENCIA, RESPOSTA_UNICA_POR_ITEM, CONTRADICAO e NOME_DE_PESSOA;
                    revisao_expr = "or" de todas as expr; revisao_pergunta_expr = "or" das que bloqueiam;
                    revisao_pergunta = textos das que bloqueiam, separados por " | ";
  revisao_pergunta_expr (Fase 13) JSON Logic; verdadeira = a revisao_pergunta é feita e a minuta fica bloqueada até a
                    resposta. Falta de resposta só destaca (revisao_expr), nunca bloqueia: a pendência que decide bloco
                    já aparece como pergunta do wizard.
Linhas novas: complementos do operador CK-X-01 a CK-X-09 (checklist = COMPLEMENTO), das sugestões S10 a S18.
S21: perguntas 10.1 a 10.11 do consumo (comodato) viram SO_CONTROLE, sem efeito na minuta.
revisao_expr é avaliada depois da leitura, do preenchimento (M11) e do cálculo dos itens (M05), com os mesmos dados das
validações do M10. Metadados da leitura (P32): checklist.marcas_multiplas, checklist.resposta_unica_por_item e
checklist.divergencias_leitura (listas de IDs do M11) e CK_x_numero (número lido do texto de 'Outro').
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv, ler_csv  # noqa: E402
from f10_m11_regras import SIM_NAO_DEST  # noqa: E402
from jlogic import dumps, e, eq, inn, nao, ne, ou, tem, var, vazio  # noqa: E402

SIM, NAO = "Sim", "Não"
MARCAS = "checklist.marcas_multiplas"
UNICA_POR_ITEM = "checklist.resposta_unica_por_item"
DIVERG = "checklist.divergencias_leitura"
COMODATO = [f"CK-C-10.{n}" for n in range(1, 12)]
FONTE_0009 = ("Decisão 0009 (23/10/2026): o checklist distribuído não muda; leitura, revisão e complementos ficam no M11. "
              "Sugestão de origem em sugestoes_checklist.md.")


def ckn(cid):
    return "CK_" + cid[3:].replace("-", "_").replace(".", "_")


def lista_ids(nome):
    return var(nome, [])


LEITURA_TIPO = {
    "SIM_NAO": "Uma marca, Sim ou Não. Duas marcas: resposta vazia, ID em checklist.marcas_multiplas e destaque. Nenhuma "
               "marca: sem resposta.",
    "UNICA": "Uma opção. Duas ou mais marcas: resposta vazia, ID em checklist.marcas_multiplas e destaque. Texto escrito ao "
             "lado de 'Outro' em CK_x_texto.",
    "MULTIPLA": "Todas as opções marcadas, em lista. Texto escrito ao lado de 'Outro' em CK_x_texto.",
    "TEXTO": "Texto da caixa de resposta, sem alteração.",
    "NUMERO": "Número escrito. O que não for número fica vazio e destacado.",
    "TABELA": "Uma entrada por linha preenchida da tabela, com os campos da pergunta.",
}

# leitura própria (acrescentada à leitura do tipo) e revisão específica: id -> (texto, expr, pergunta)
ESPEC = {}


# Fase 14: um texto por motivo de revisão. MOTIVOS[cid] = [(motivo, expr, texto, bloqueia)]; bloqueia segue a P34
# (só a dúvida que muda a minuta, isto é, a que tem pergunta ao operador).
MOTIVOS_FIXOS = ("SEM_RESPOSTA", "MARCAS_MULTIPLAS", "OUTRO_ILEGIVEL", "DIVERGENCIA", "RESPOSTA_UNICA_POR_ITEM",
                 "CONTRADICAO", "NOME_DE_PESSOA")
MOTIVOS = {}


def _motivo(cid, motivo, expr, texto, pergunta):
    if expr is None:
        return
    if motivo not in MOTIVOS_FIXOS:
        raise SystemExit(f"{cid}: motivo de revisão {motivo} fora da lista fixa")
    MOTIVOS.setdefault(cid, []).append((motivo, expr, pergunta or texto, bool(pergunta)))


def espec(cid, texto, expr=None, pergunta="", motivo=None):
    ESPEC[cid] = (texto, expr, pergunta)
    _motivo(cid, motivo, expr, texto, pergunta)


# S01: armazenamento
espec("CK-C-13.5", "Duplicidade com a 20.1 (S01): prevalece a 13.5; resposta diferente na 20.1 destaca as duas (VAL-022).",
      e(tem("CK_C_13_5"), tem("CK_C_20_1"), ne("CK_C_13_5", var("CK_C_20_1"))), motivo="DIVERGENCIA")
espec("CK-C-20.1", "Repete a 13.5 (S01): não preenche nada; só confere. Resposta diferente da 13.5 destaca as duas.",
      e(tem("CK_C_13_5"), tem("CK_C_20_1"), ne("CK_C_13_5", var("CK_C_20_1"))), motivo="DIVERGENCIA")
# S02: fabricantes e fornecedores
for L in ("C", "P"):
    div = ou(e(eq(f"CK_{L}_6_1", NAO), ou(eq(f"CK_{L}_5_5", SIM), eq(f"CK_{L}_5_6", SIM))),
             e(eq(f"CK_{L}_6_1", SIM), eq(f"CK_{L}_5_5", NAO), eq(f"CK_{L}_5_6", NAO)))
    espec(f"CK-{L}-6.1", "Repete a 5.5 e a 5.6 (S02): prevalecem a 5.5 e a 5.6; a 6.1 só confere. Contradição destaca a 6.1 "
                         "(VAL-023).", div, motivo="CONTRADICAO")
    for n in ("5.5", "5.6"):
        espec(f"CK-{L}-{n}", "Prevalece sobre a 6.1 em caso de divergência (S02).", None)
    # S03: cabeçalho x seção 1
    espec(f"CK-{L}-CAB.02", "Duplicidade com a 1.1 (S03): prevalece a 1.1; com as duas respondidas e diferentes, as duas "
                            "ficam destacadas.", e(tem(f"CK_{L}_CAB_02"), tem(f"CK_{L}_1_1"),
                                                   ne(f"CK_{L}_CAB_02", var(f"CK_{L}_1_1"))), motivo="DIVERGENCIA")
    espec(f"CK-{L}-1.1", "Prevalece sobre o cabeçalho (S03).", e(tem(f"CK_{L}_CAB_02"), tem(f"CK_{L}_1_1"),
                                                                ne(f"CK_{L}_CAB_02", var(f"CK_{L}_1_1"))), motivo="DIVERGENCIA")
    espec(f"CK-{L}-CAB.04", "Duplicidade com a 1.4 (S03): prevalece a 1.4. A leitura compara o nome do cabeçalho com o "
                            "campo Nome da 1.4; diferença põe os dois IDs em checklist.divergencias_leitura. Responsável só "
                            "no cabeçalho (1.4 vazia) também é destacado.",
          ou(inn(f"CK-{L}-CAB.04", lista_ids(DIVERG)), e(tem(f"CK_{L}_CAB_04"), vazio(f"CK_{L}_1_4"))), motivo="DIVERGENCIA")
    espec(f"CK-{L}-1.4", "Prevalece sobre o cabeçalho (S03); telefone e e-mail ficam só no processo.",
          inn(f"CK-{L}-1.4", lista_ids(DIVERG)), motivo="DIVERGENCIA")
# S04
espec("CK-C-12.2", "Lida como 'o prazo da 12.1 é diferente de 30 dias?' (S04, DV-28): Sim = diferente, Não = igual. A "
                   "explicação é pedida quando a VAR-060 (prazo da 12.1) é diferente do PAR-05. Resposta que contradiz o "
                   "prazo da 12.1 fica destacada.",
      ou(e(eq("CK_C_12_2", NAO), tem("VAR_060"), ne("VAR_060", var("parametros.prazo_entrega_referencia"))),
         e(eq("CK_C_12_2", SIM), eq("VAR_060", var("parametros.prazo_entrega_referencia")))), motivo="CONTRADICAO")
# S06
espec("CK-C-7.2", "Mistura resposta e causa (S06): 'Não' sozinho = demanda estável; 'Sim' ou qualquer causa marcada = "
                  "demanda variável (sugere registro de preços, VAL-024). 'Não' junto com outra marca é contradição e fica "
                  "destacada.",
      e(inn(NAO, var("CK_C_7_2", [])), {"some": [var("CK_C_7_2", []), ne(var(""), NAO)]}), motivo="CONTRADICAO")
# S07
P07 = {"CK-C-14.1": "O prazo total de validade veio numa resposta só e marcou todos os itens de consumo como perecíveis. "
                    "Quais itens têm prazo de validade?",
       "CK-C-14.2": "A validade mínima na entrega veio numa resposta só e foi aplicada a todos os itens de consumo. Confirme "
                    "ou corrija a validade mínima de cada item.",
       "CK-P-13.1": "A garantia mínima veio numa resposta só e foi aplicada a todos os itens permanentes. Confirme ou corrija "
                    "a garantia de cada item, em meses."}
for cid, perg in P07.items():
    espec(cid, "Por item (S07). Se o Word trouxer uma resposta só, sem indicar itens, ela vale para todos os itens do "
               "checklist (consumo ou permanentes), o ID entra em checklist.resposta_unica_por_item e a resposta fica "
               "destacada pedindo confirmação item a item.", inn(cid, lista_ids(UNICA_POR_ITEM)), perg, motivo="RESPOSTA_UNICA_POR_ITEM")
# S08: perguntas 'Quem...'
for cid in ("CK-C-9.7", "CK-C-16.5", "CK-P-11.6", "CK-P-17.5", "CK-P-19.6"):
    espec(cid, "Pergunta 'Quem...' (S08): a resposta fica só para controle e nunca vai à minuta. Fica destacada sempre que "
               "houver resposta, para o operador ver que nome de pessoa não sai do sistema; a leitura não separa nome de "
               "cargo sem um detector no motor (P32).", tem(ckn(cid)), motivo="NOME_DE_PESSOA")
# S09: seções 8 e 11
espec("CK-C-8.2", "Grupo de itens diferentes, não divisão do mesmo item (S09). Sim sem item indicado, ou Sim com a 8.1 = Sim "
                  "(itens podem ser fornecidos separadamente), parece resposta trocada com a seção 11 e fica destacada.",
      ou(e(eq("CK_C_8_2", SIM), {"none": [var("itens"), tem("grupo")]}), e(eq("CK_C_8_1", SIM), eq("CK_C_8_2", SIM))),
      "A pergunta 8.2 pede grupo de itens, mas nenhum item foi indicado ou a 8.1 diz que os itens podem ser fornecidos "
      "separadamente. Quais itens formam cada grupo? Se a resposta tratava da divisão de um mesmo item (seção 11), deixe "
      "sem grupo.", motivo="CONTRADICAO")
espec("CK-C-8.1", "Contradição com a 8.2 (S09): 8.1 = Sim e 8.2 = Sim ficam destacadas.",
      e(eq("CK_C_8_1", SIM), eq("CK_C_8_2", SIM)), motivo="CONTRADICAO")
for n in ("11.2", "11.4"):
    cid = f"CK-C-{n}"
    espec(cid, "Divisão do mesmo item entre fornecedores, isto é, cota (S09). Sim sem nenhuma unidade de disputa acima do "
               "limite de participação exclusiva (sem cota possível) parece resposta sobre grupo e fica destacada.",
          e(eq(ckn(cid), SIM), {"some": [var("itens"), tem("valor_unidade_disputa")]},
            {"none": [var("itens"), {">": [var("valor_unidade_disputa"), var("parametros.limite_exclusivo_me_epp")]}]}), motivo="CONTRADICAO")
# S20: 'Outro' do prazo de entrega
for cid in ("CK-C-12.1", "CK-P-8.1"):
    n = ckn(cid)
    espec(cid, "'Outro' do prazo (S20): se o texto escrito for número seguido de 'dias' (ex.: '45 dias'), a leitura põe o "
               f"número em {n}_numero e ele é o prazo (VAR-060); qualquer outra coisa deixa {n}_numero vazio, destaca a "
               "resposta e faz a pergunta ao operador. A leitura do número é função do motor (P32), não expressão.",
          e(eq(n, "Outro"), vazio(n + "_numero")),
          "O prazo de entrega marcado como 'Outro' não está escrito como número de dias (ex.: '45 dias'). Qual é o prazo "
          "de entrega, em dias corridos?", motivo="OUTRO_ILEGIVEL")

# P32.1 (resposta de 23/10/2026): a mesma leitura do número vale para os outros 'Outro' de prazo e de garantia
def espec_mais(cid, texto, expr, pergunta="", motivo=None):
    _motivo(cid, motivo, expr, texto, pergunta)
    t0, e0, p0 = ESPEC.get(cid, ("", None, ""))
    ESPEC[cid] = ((t0 + " " + texto).strip(), ou(e0, expr) if e0 is not None else expr,
                  (p0 + " " + pergunta).strip() if p0 and pergunta else (p0 or pergunta))


for cid, outro, unid, perg in (
        ("CK-C-16.3", "Outro", "dias", "Qual é o prazo para substituir o produto recusado, em dias?"),
        ("CK-P-19.5", "Outro", "dias", "Qual é o prazo de correção ou substituição, em dias?"),
        ("CK-P-19.3", "Outro", "dias úteis", "Qual é o prazo para os testes e a avaliação definitiva, em dias úteis?"),
        ("CK-P-13.7", "Outro", "dias úteis", "Qual é o prazo para restabelecer o funcionamento, em dias úteis?"),
        ("CK-P-13.1", "Outro: ______ meses", "meses", "Se houver 'Outro' sem número de meses legível: qual é a garantia "
                                                      "mínima de cada item, em meses?")):
    n = ckn(cid)
    espec_mais(cid, f"'Outro' (P32.1): número seguido de '{unid}' vira o número em {n}_numero e é o valor; qualquer outra "
                    f"coisa deixa {n}_numero vazio, destaca a resposta e faz a pergunta ao operador.",
               e(eq(n, outro), vazio(n + "_numero")),
               f"O 'Outro' desta pergunta não traz um número legível. {perg}", motivo="OUTRO_ILEGIVEL")
espec_mais("CK-P-19.3", "A opção '30 dias' está em dias corridos e o prazo de recebimento definitivo é contado em dias "
                        "úteis: não é convertida, fica destacada e vira pergunta.", eq("CK_P_19_3", "30 dias"),
           "A opção '30 dias' está em dias corridos, mas o prazo de recebimento definitivo é em dias úteis. Qual é o prazo "
           "em dias úteis?", motivo="CONTRADICAO")

# --------------------------------------------------------------------------- complementos (S10 a S18)
CONSUMO, PERMANENTES = tem("checklist.consumo"), tem("checklist.permanentes")
COMPL = [
    # id, sugestão, pergunta, tipo, opções, por_item, condicional (texto, expr), destinos, efeito, regra, expressão
    ("CK-X-01", "S10", "Onde os itens serão entregues? Informe OMS, setor de recebimento, endereço e horário; se houver mais "
     "de um local, informe os itens de cada local.", "TEXTO", "", "N",
     ("responder se o checklist de consumo foi recebido", CONSUMO), "VAR-064; TR-5.4", "PREENCHE",
     "O checklist de consumo não pede o local de entrega; o texto vai para a VAR-064 (NE-026 nota 2).",
     {"VAR_064": var("CK_X_01")}),
    ("CK-X-02", "S11", "Se a entrega for parcelada ou conforme pedidos, informe as parcelas (itens, quantidades e prazos) ou "
     "o critério dos pedidos.", "TEXTO", "", "N",
     ("responder se CK-C-12.3 = Parcelada ou Conforme pedidos da unidade",
      inn(var("CK_C_12_3"), ["Parcelada", "Conforme pedidos da unidade"])),
     "VAR-062; TR-5.2.TAB1", "PREENCHE", "Composição das parcelas ou critério dos pedidos para a VAR-062.",
     {"VAR_062": var("CK_X_02")}),
    ("CK-X-03", "S12", "Quantos dias úteis a equipe técnica precisa para concluir a avaliação definitiva do recebimento?",
     "NUMERO", "", "N", ("responder se o checklist de consumo foi recebido", CONSUMO), "VAR-075; WZ-34; TR-8.3",
     "PREENCHE", "Número de dias úteis digitado, sem opção pré-definida (decisão 0009); vai para a VAR-075. A WZ-34 é "
     "resposta composta e continua com a equipe.", {"VAR_075": var("CK_X_03")}),
    ("CK-X-04", "S13", "Quais critérios de sustentabilidade do Guia Nacional de Contratações Sustentáveis se aplicam? "
     "Informe item, requisito e forma de comprovação.", "TEXTO", "", "N",
     ("responder se o checklist de consumo foi recebido", CONSUMO), "VAR-044; WZ-17; TR-4.1.1", "PREENCHE",
     "Critérios informados vão para a VAR-044 e marcam WZ-17 = SIM, como a 21.4 do checklist de permanentes (NE-011).",
     {"VAR_044": var("CK_X_04"), "WZ_17": "SIM"}),
    ("CK-X-05", "S14", "Qual o prazo de garantia técnica deste item, em meses?", "NUMERO", "", "S",
     ("responder se CK-C-18.1 = Sim", eq("CK_C_18_1", SIM)), "VAR-124", "PREENCHE",
     "Prazo por item para garantia_minima_meses, nos itens indicados pelo operador.",
     {"itens.garantia_minima_meses": var("CK_X_05")}),
    ("CK-X-06", "S15", "Qual o código CATMAT deste item?", "TEXTO", "", "S",
     ("responder se algum item estiver sem CATMAT", {"some": [var("itens"), vazio("catmat")]}), "VAR-157; TR-1.1.TAB1",
     "PREENCHE", "Código digitado pelo operador; item sem código continua na VAL-039.",
     {"itens.catmat": var("CK_X_06")}),
    ("CK-X-07", "S16", "Este item é de consumo ou permanente?", "UNICA", "CONSUMO; PERMANENTE", "S",
     ("responder se vieram os dois checklists", e(CONSUMO, PERMANENTES)), "VAR-155; WZ-07; VAL-040", "PREENCHE",
     "Categoria do item quando o processo tem os dois checklists (domínio da VAR-155).",
     {"itens.categoria": var("CK_X_07")}),
    ("CK-X-08", "S17", "Quais OMS poderão usar a contratação e, se souber, com que quantidades estimadas por item?", "TEXTO",
     "", "N", ("responder se CK-C-7.6 = Sim", eq("CK_C_7_6", SIM)), "VAR-029; WZ-11; WZ-12", "SUGERE",
     "Apoio para a WZ-11, a WZ-12 e a VAR-029; a confirmação vem da IRP.", {"VAR_029": var("CK_X_08")}),
    ("CK-X-09", "S18", "Este item exige faixa de temperatura ou umidade no transporte e na guarda até a instalação? "
     "Informe a faixa.", "TEXTO", "", "S", ("responder se o checklist de permanentes foi recebido", PERMANENTES),
     "VAR-122; SET-02", "PREENCHE", "Faixa por item para faixa_temperatura, como a 13.1 do checklist de consumo.",
     {"itens.faixa_temperatura": var("CK_X_09")}),
]


# Fase 15 (P38): partes de cláusula do M08 que nenhuma pergunta do checklist dá. Só aparecem quando a cláusula entra
# (condicional = condicao_expr da cláusula). O mapa da cláusula (M08.lacunas_mapa) lê o complemento direto; ele não
# soma à VAR da cláusula, para não repetir texto.
COMPL_M08 = [
    # id, cláusula, VAR da parte, pergunta, tipo, opções
    ("CK-X-10", "SET-03", "VAR-130", "Quais itens serão entregues acompanhados dos documentos indicados no checklist "
     "(certificado de análise do lote, laudo, documento de rastreabilidade, registro de temperatura)?", "MULTIPLA",
     "números dos itens da tabela"),
    ("CK-X-11", "SET-07", "VAR-135", "Quais itens devem atender aos requisitos sanitários e técnicos indicados no "
     "checklist?", "MULTIPLA", "números dos itens da tabela"),
    ("CK-X-12", "SET-07", "VAR-135", "Os requisitos sanitários e técnicos serão comprovados na proposta ou na entrega?",
     "UNICA", "na proposta; na entrega; na proposta e na entrega"),
    ("CK-X-13", "SET-08", "VAR-136", "Qual atividade da empresa fornecedora depende da autorização exigida (ex.: "
     "distribuição ou comércio dos produtos)?", "TEXTO", ""),
    ("CK-X-14", "SET-08", "VAR-136", "Qual órgão expede essa autorização (ex.: vigilância sanitária ou Anvisa)?", "TEXTO",
     ""),
    ("CK-X-15", "SET-09", "VAR-131", "Com qual setor a entrega será agendada?", "TEXTO", ""),
    ("CK-X-16", "SET-09", "VAR-131", "Com quanta antecedência mínima a entrega deve ser agendada (número e unidade, ex.: "
     "48 horas)?", "TEXTO", ""),
    ("CK-X-17", "SET-10", "VAR-132", "Quais itens têm entrega emergencial?", "MULTIPLA", "números dos itens da tabela"),
    ("CK-X-18", "SET-11", "VAR-137", "Em quais itens o Contratado executará a montagem, a instalação e as demais "
     "atividades?", "MULTIPLA", "números dos itens da tabela"),
    ("CK-X-19", "SET-18", "VAR-144", "Qual equipamento será desinstalado e retirado, e em que local?", "TEXTO", ""),
]


def generica(r, cond):
    """S05: duas marcas em pergunta de uma opção; nenhuma resposta em pergunta a responder."""
    partes = []
    if r["tipo_resposta"] in ("UNICA", "SIM_NAO"):
        partes.append(inn(r["id"], lista_ids(MARCAS)))
    sem = vazio(ckn(r["id"]))
    partes.append(e(cond, sem) if cond is not None else sem)
    return ou(*partes)


def motivos_da_linha(r, cond):
    """[(motivo, expr, texto, bloqueia)]: os específicos (MOTIVOS) e os gerais (sem resposta, duas marcas)."""
    cid = r["id"]
    lista = {"CONSUMO": "consumo", "PERMANENTES": "permanentes"}.get(r["checklist"], r["checklist"].lower())
    out = list(MOTIVOS.get(cid, []))
    if r["efeito"] == "SO_CONTROLE":
        return out
    if r["tipo_resposta"] in ("UNICA", "SIM_NAO"):
        opc = r["opcoes"].split("campos:")[0].strip().rstrip(";")
        if r["efeito"] == "PREENCHE" and r["preenche_expr"]:
            out.append(("MARCAS_MULTIPLAS", inn(cid, lista_ids(MARCAS)),
                        f"Na pergunta {r['numero']} do checklist de {lista} a leitura achou mais de uma marca. Qual opção "
                        f"vale: {opc}?", True))
        else:
            out.append(("MARCAS_MULTIPLAS", inn(cid, lista_ids(MARCAS)),
                        f"Na pergunta {r['numero']} do checklist de {lista} a leitura achou mais de uma marca; a "
                        f"resposta não muda a minuta. Confira no Word.", False))
    sem = vazio(ckn(cid))
    out.append(("SEM_RESPOSTA", e(cond, sem) if cond is not None else sem,
                f"A pergunta {r['numero']} do checklist de {lista} está sem resposta. Confira no Word; se ela decide "
                f"um bloco da minuta, o wizard pergunta.", False))
    return out


def main():
    pasta = Path(sys.argv[1])
    m11 = ler_csv(pasta / "M11_checklist.csv")
    log = []
    novas = ("leitura", "revisao_expr", "revisao_pergunta", "revisao_pergunta_expr", "revisao_motivos")
    cols = [c for c in m11[0] if c not in novas]
    k = cols.index("sugere_expr") + 1
    cols = cols[:k] + list(novas) + cols[k:]
    alimenta = {}
    for (cid_, d_), dec_ in SIM_NAO_DEST.items():
        if dec_[0] == "DETALHE":
            alimenta.setdefault(d_, []).append(cid_)
    ids = {r["id"] for r in m11}
    for cid in ESPEC:
        if cid not in ids:
            raise SystemExit(f"leitura para pergunta inexistente: {cid}")
    for r in m11:
        cid = r["id"]
        if cid in COMODATO:
            r["regra"] = ("Comodato fora do sistema por enquanto (S21; decisões 0008 e 0009): resposta lida e guardada só "
                          f"para controle, sem efeito na minuta. Destinos antes do desligamento: {r['destinos'] or 'nenhum'}. "
                          f"Regra anterior: {r['regra']}")
            r.update(efeito="SO_CONTROLE", destinos="", preenche_expr="", sugere_expr="")
        texto, expr, perg = ESPEC.get(cid, ("", None, ""))
        leit = ("Lida e guardada só para controle; não vai para a minuta." if r["efeito"] == "SO_CONTROLE"
                else LEITURA_TIPO[r["tipo_resposta"]])
        if r["por_item"] == "S" and cid not in P07:
            leit += " Por item: cada resposta fica ligada aos itens que ela indica."
        sn = sorted((d_, dec_) for (c_, d_), dec_ in SIM_NAO_DEST.items() if c_ == cid)
        det = [(d_, dec_[1]) for d_, dec_ in sn if dec_[0] == "DETALHE"]
        if det:
            leit += (f" Texto da caixa 'Resposta:' em {ckn(cid)}_texto (Fase 13); vai para "
                     + " e ".join(f"a {d_}" for d_, _ in det) + f" só com a resposta '{det[0][1]}'.")
        r["leitura"] = (leit + " " + texto).strip()
        if sn and "Fase 13 (23/10/2026)" not in r["regra"]:
            partes_r = []
            for d_, dec_ in sn:
                if dec_[0] == "DETALHE":
                    outras = [c_ for c_ in alimenta[d_] if c_ != cid]
                    partes_r.append(f"{d_} recebe o texto da caixa de resposta, não a opção"
                                    + (f"; acumula com {', '.join(outras)}, na ordem do M11, sem prevalência" if outras
                                       else ""))
                else:
                    partes_r.append(f"{d_} não recebe a resposta ({'só condição' if dec_[0] == 'CONDICAO' else 'fica com a equipe'}: {dec_[1]})")
            r["regra"] = r["regra"].rstrip() + " Fase 13 (23/10/2026), Sim/Não fora de campo de texto: " + "; ".join(partes_r) + "."
        cond = json.loads(r["condicional_expr"]) if r["condicional_expr"] else None
        # Fase 14: revisao_motivos (um texto por motivo); as três colunas de antes são o resumo
        mot = motivos_da_linha(r, cond)
        r["revisao_motivos"] = json.dumps([{"motivo": m, "expr": x, "texto": t, "bloqueia": b} for m, x, t, b in mot],
                                          ensure_ascii=False, separators=(",", ":")) if mot else ""
        r["revisao_expr"] = dumps(ou(*[x for _, x, _, _ in mot])) if mot else ""
        bloq = [(x, t) for _, x, t, b in mot if b]
        r["revisao_pergunta_expr"] = dumps(ou(*[x for x, _ in bloq])) if bloq else ""
        r["revisao_pergunta"] = " | ".join(t for _, t in bloq)
        if "Fase 11 (23/10/2026)" not in r["fonte"]:
            r["fonte"] = r["fonte"].rstrip() + " Fase 11 (23/10/2026): leitura, revisao_expr e revisao_pergunta. " + FONTE_0009
        if "Fase 13 (23/10/2026): revisao_pergunta_expr" not in r["fonte"] and r["revisao_pergunta_expr"]:
            r["fonte"] = (r["fonte"].rstrip() + " Fase 13 (23/10/2026): revisao_pergunta_expr separa o destaque (falta de "
                          "resposta) da pergunta que bloqueia (dúvida que muda a minuta); decisão do gestor, a confirmar "
                          "com o dono do projeto (P34).")
    for (cid, s_, perg, tipo, opc, por_item, (ctexto, cexpr), dest, ef, regra, ex) in COMPL:
        if cid in ids:
            raise SystemExit(f"{cid} já existe")
        m11.append({"id": cid, "checklist": "COMPLEMENTO", "secao": "COMPLEMENTO DO OPERADOR (decisão 0009)",
                    "numero": cid[5:].replace("-", "."), "pergunta": perg, "tipo_resposta": tipo, "opcoes": opc,
                    "orientacao": "Preenchido pelo operador no sistema; não existe no Word distribuído.",
                    "condicional": ctexto, "condicional_expr": dumps(cexpr), "por_item": por_item, "destinos": dest,
                    "efeito": ef, "regra": f"Complemento do operador ({s_}). {regra}",
                    "preenche_expr": dumps(ex) if ef == "PREENCHE" else "",
                    "sugere_expr": dumps(ex) if ef == "SUGERE" else "",
                    "leitura": "Digitado pelo operador no sistema (complemento). " + LEITURA_TIPO[tipo]
                               + (" Por item: o operador indica os itens." if por_item == "S" else ""),
                    "revisao_expr": "", "revisao_pergunta": "", "revisao_pergunta_expr": "", "revisao_motivos": "",
                    "fonte": f"Sugestão {s_} (sugestoes_checklist.md), aceita pelo dono do projeto em 23/10/2026 (decisão 0009). {FONTE_0009} "
                             f"Pergunta, destinos e expressão INFERIDOS.", "status": "INFERIDO"})
    m08 = {x["id"]: x for x in ler_csv(pasta / "M08_clausulas_setoriais.csv")}
    for (cid, sid, vid, perg, tipo, opc) in COMPL_M08:
        if cid in ids or cid in {x["id"] for x in m11}:
            raise SystemExit(f"{cid} já existe")
        c8 = m08[sid]
        m11.append({"id": cid, "checklist": "COMPLEMENTO", "secao": "COMPLEMENTO DO OPERADOR (decisão 0009)",
                    "numero": cid[5:].replace("-", "."), "pergunta": perg, "tipo_resposta": tipo, "opcoes": opc,
                    "orientacao": "Preenchido pelo operador no sistema; não existe no Word distribuído.",
                    "condicional": f"responder se a {sid} entrar na minuta (mesma condição: {c8['condicao']})",
                    "condicional_expr": c8["condicao_expr"], "por_item": "N", "destinos": f"{vid}; {sid}",
                    "efeito": "PREENCHE",
                    "regra": f"Complemento do operador (P38, Fase 15): parte da {sid} ligada à {vid} que nenhuma pergunta "
                             f"do checklist dá. O lacunas_mapa da {sid} lê a resposta ({ckn(cid)}) direto no marcador; "
                             f"ela não soma à {vid}, para o texto não repetir.",
                    "preenche_expr": "", "sugere_expr": "",
                    "leitura": "Digitado pelo operador no sistema (complemento). " + (
                        "Números dos itens da tabela, em lista." if tipo == "MULTIPLA" else LEITURA_TIPO[tipo]),
                    "revisao_expr": "", "revisao_pergunta": "", "revisao_pergunta_expr": "", "revisao_motivos": "",
                    "fonte": f"P38 (perguntas_abertas.md), resposta de 24/10/2026: partes do M08 com fonte nula viram "
                             f"complementos do operador, como os CK-X-01 a CK-X-09 (decisão 0009). Pergunta INFERIDA do "
                             f"marcador da {sid}.", "status": "INFERIDO"})
    gravar_csv(pasta / "M11_checklist.csv", cols, m11, preservar=())
    log.append(f"M11: {len(m11)} linhas; complementos {len(COMPL)}; leitura em {sum(1 for r in m11 if r['leitura'])}; "
               f"revisao_expr em {sum(1 for r in m11 if r['revisao_expr'])}; revisao_pergunta em "
               f"{sum(1 for r in m11 if r['revisao_pergunta'])} (bloqueiam só com revisao_pergunta_expr: "
               f"{sum(1 for r in m11 if r['revisao_pergunta_expr'])}); SO_CONTROLE do comodato: {len(COMODATO)}")
    Path(sys.argv[2]).write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))


# --------------------------------------------------------------------------- casos de teste (f11 nos testes)
def dados_condicional(cond):
    """dados mínimos que tornam a condicional verdadeira (formas usadas no M11)."""
    if cond is None:
        return {}
    op, a = next(iter(cond.items()))
    if op == "==" and isinstance(a[0], dict) and "var" in a[0]:
        return {a[0]["var"]: a[1]}
    if op == "in" and isinstance(a[0], dict):
        return {a[0]["var"]: a[1][0]}
    if op == "and":
        d = {}
        for x in a:
            d.update(dados_condicional(x))
        return d
    if op == "!!":
        nome = a[0]["var"]
        if nome.startswith("checklist."):
            return {"checklist": {nome.split(".", 1)[1]: True}}
        return {nome: "45 dias"}
    if op == "!=":
        return {a[0]["var"]: 45}
    if op == "some":
        return {"itens": [{"garantia_minima_meses": 36}]}
    raise ValueError(f"condicional sem caso de teste: {cond}")


def resposta_valida(r):
    ops = [o.strip() for o in r["opcoes"].split("campos:")[0].split(";") if o.strip()]
    if r["tipo_resposta"] == "MULTIPLA":
        return [ops[0]]
    if r["tipo_resposta"] in ("UNICA", "SIM_NAO"):
        return ops[0]
    if r["tipo_resposta"] == "NUMERO":
        return 1
    if r["tipo_resposta"] == "TABELA":
        return [{"campo": "x"}]
    return "resposta de teste"


CASOS_ESPECIFICOS = {
    # id: [(dados, dispara)]
    "CK-C-13.5": [({"CK_C_13_5": SIM, "CK_C_20_1": NAO}, True), ({"CK_C_13_5": SIM, "CK_C_20_1": SIM}, False)],
    "CK-C-20.1": [({"CK_C_13_5": NAO, "CK_C_20_1": SIM}, True), ({"CK_C_13_5": NAO, "CK_C_20_1": NAO}, False)],
    "CK-C-6.1": [({"CK_C_6_1": NAO, "CK_C_5_5": SIM}, True), ({"CK_C_6_1": SIM, "CK_C_5_5": SIM, "CK_C_5_6": NAO}, False)],
    "CK-P-6.1": [({"CK_P_6_1": SIM, "CK_P_5_5": NAO, "CK_P_5_6": NAO}, True), ({"CK_P_6_1": NAO, "CK_P_5_5": NAO,
                                                                              "CK_P_5_6": NAO}, False)],
    "CK-C-CAB.02": [({"CK_C_CAB_02": "OMS A", "CK_C_1_1": "OMS B"}, True), ({"CK_C_CAB_02": "OMS A",
                                                                           "CK_C_1_1": "OMS A"}, False)],
    "CK-C-CAB.04": [({"CK_C_CAB_04": "[RESPONSÁVEL]"}, True),
                    ({"CK_C_CAB_04": "[RESPONSÁVEL]", "CK_C_1_4": [{"Nome": "[RESPONSÁVEL]"}]}, False),
                    ({"CK_C_CAB_04": "[RESPONSÁVEL]", "CK_C_1_4": [{"Nome": "[OUTRO]"}],
                      "checklist": {"divergencias_leitura": ["CK-C-CAB.04"]}}, True)],
    "CK-C-12.2": [({"CK_C_12_2": NAO, "VAR_060": 45}, True), ({"CK_C_12_2": SIM, "VAR_060": 30}, True),
                  ({"CK_C_12_2": SIM, "VAR_060": 45}, False), ({"CK_C_12_2": NAO, "VAR_060": 30}, False)],
    "CK-C-7.2": [({"CK_C_7_2": [NAO, "Consumo imprevisível"]}, True), ({"CK_C_7_2": [NAO]}, False),
                 ({"CK_C_7_2": [SIM, "Consumo imprevisível"]}, False)],
    "CK-C-14.2": [({"CK_C_14_2": "12 meses", "checklist": {"resposta_unica_por_item": ["CK-C-14.2"]}}, True),
                  ({"CK_C_14_2": "12 meses"}, False)],
    "CK-P-13.1": [({"CK_P_13_1": "36 meses", "checklist": {"resposta_unica_por_item": ["CK-P-13.1"]}}, True),
                  ({"CK_P_13_1": "Outro: ______ meses"}, True),
                  ({"CK_P_13_1": "Outro: ______ meses", "CK_P_13_1_numero": 48}, False),
                  ({"CK_P_13_1": "36 meses"}, False)],
    "CK-C-9.7": [({"CK_C_9_7": "[RESPONSÁVEL]"}, True), ({}, False)],
    "CK-C-8.2": [({"CK_C_8_2": SIM, "itens": [{"numero": 1}]}, True),
                 ({"CK_C_8_2": SIM, "CK_C_8_1": SIM, "itens": [{"numero": 1, "grupo": "G1"}]}, True),
                 ({"CK_C_8_2": SIM, "CK_C_8_1": NAO, "itens": [{"numero": 1, "grupo": "G1"}]}, False)],
    "CK-C-11.2": [({"CK_C_11_2": SIM, "itens": [{"valor_unidade_disputa": 5000}]}, True),
                  ({"CK_C_11_2": SIM, "itens": [{"valor_unidade_disputa": 150000}]}, False)],
    "CK-C-12.1": [({"CK_C_12_1": "Outro", "CK_C_12_1_texto": "conforme a necessidade"}, True),
                  ({"CK_C_12_1": "Outro", "CK_C_12_1_texto": "45 dias", "CK_C_12_1_numero": 45}, False),
                  ({"CK_C_12_1": "15 dias"}, False)],
    "CK-C-16.3": [({"CK_C_16_3": "Outro", "CK_C_16_3_texto": "imediato"}, True),
                  ({"CK_C_16_3": "Outro", "CK_C_16_3_numero": 3}, False), ({"CK_C_16_3": "2 dias"}, False)],
    "CK-P-19.5": [({"CK_P_19_5": "Outro"}, True), ({"CK_P_19_5": "Outro", "CK_P_19_5_numero": 15}, False)],
    "CK-P-19.3": [({"CK_P_19_3": "Outro"}, True), ({"CK_P_19_3": "30 dias"}, True),
                  ({"CK_P_19_3": "Outro", "CK_P_19_3_numero": 20}, False), ({"CK_P_19_3": "5 dias úteis"}, False)],
    "CK-P-13.7": [({"CK_P_13_7": "Outro"}, True), ({"CK_P_13_7": "Outro", "CK_P_13_7_numero": 3}, False)],
    "CK-P-8.1": [({"CK_P_8_1": "Outro", "CK_P_8_1_texto": "a combinar"}, True),
                 ({"CK_P_8_1": "Outro", "CK_P_8_1_numero": 75}, False)],
}


for _L in ("C", "P"):
    CASOS_ESPECIFICOS.setdefault(f"CK-{_L}-CAB.02", [({f"CK_{_L}_CAB_02": "OMS A", f"CK_{_L}_1_1": "OMS B"}, True),
                                                   ({f"CK_{_L}_CAB_02": "OMS A", f"CK_{_L}_1_1": "OMS A"}, False)])
    CASOS_ESPECIFICOS[f"CK-{_L}-1.1"] = [({f"CK_{_L}_CAB_02": "OMS A", f"CK_{_L}_1_1": "OMS B"}, True),
                                         ({f"CK_{_L}_1_1": "OMS A"}, False)]
    CASOS_ESPECIFICOS.setdefault(f"CK-{_L}-CAB.04", [({f"CK_{_L}_CAB_04": "[RESPONSÁVEL]"}, True),
                                                   ({f"CK_{_L}_CAB_04": "[RESPONSÁVEL]",
                                                     f"CK_{_L}_1_4": [{"Nome": "[RESPONSÁVEL]"}]}, False)])
    CASOS_ESPECIFICOS[f"CK-{_L}-1.4"] = [({f"CK_{_L}_1_4": [{"Nome": "[RESPONSÁVEL]"}],
                                           "checklist": {"divergencias_leitura": [f"CK-{_L}-1.4"]}}, True),
                                         ({f"CK_{_L}_1_4": [{"Nome": "[RESPONSÁVEL]"}]}, False)]
for _c in ("CK-C-16.5", "CK-P-11.6", "CK-P-17.5", "CK-P-19.6"):
    CASOS_ESPECIFICOS[_c] = [({ckn(_c): "[RESPONSÁVEL]"}, True), ({}, False)]
CASOS_ESPECIFICOS["CK-C-14.1"] = [({"CK_C_14_1": "24 meses", "checklist": {"resposta_unica_por_item": ["CK-C-14.1"]}},
                                   True), ({"CK_C_14_1": "24 meses"}, False)]
CASOS_ESPECIFICOS["CK-C-8.1"] = [({"CK_C_8_1": SIM, "CK_C_8_2": SIM}, True), ({"CK_C_8_1": SIM, "CK_C_8_2": NAO}, False)]
CASOS_ESPECIFICOS["CK-C-11.4"] = [({"CK_C_11_4": SIM, "itens": [{"valor_unidade_disputa": 5000}]}, True),
                                  ({"CK_C_11_4": SIM, "itens": [{"valor_unidade_disputa": 150000}]}, False)]


def casos(m11):
    """{id: [(dados, dispara)]}: um caso que dispara e um que não dispara para cada revisao_expr, mais os específicos."""
    out = {}
    for r in m11:
        if not r["revisao_expr"]:
            continue
        cond = json.loads(r["condicional_expr"]) if r["condicional_expr"] else None
        base = dados_condicional(cond)
        n = ckn(r["id"])
        esp = CASOS_ESPECIFICOS.get(r["id"])
        lst = [(dict(base, **d), v) for d, v in (esp or [])]
        if r["efeito"] == "SO_CONTROLE":
            lst += [] if esp else [({n: "resposta"}, True), ({}, False)]
        else:
            lst.append((dict(base), True))
            if not esp:
                lst.append((dict(base, **{n: resposta_valida(r)}), False))
            if r["tipo_resposta"] in ("UNICA", "SIM_NAO"):
                lst.append((dict(base, checklist={"marcas_multiplas": [r["id"]]}), True))
        out[r["id"]] = lst
    return out


def casos_pergunta(m11):
    """{id: [(dados, pergunta_dispara)]}: falta de resposta nunca faz a pergunta; duas marcas e os casos específicos com
    pergunta fazem."""
    out = {}
    for r in m11:
        if not r["revisao_pergunta_expr"]:
            continue
        cond = json.loads(r["condicional_expr"]) if r["condicional_expr"] else None
        base = dados_condicional(cond)
        lst = [(dict(base), False)]
        if r["tipo_resposta"] in ("UNICA", "SIM_NAO") and r["efeito"] == "PREENCHE":
            lst.append((dict(base, checklist={"marcas_multiplas": [r["id"]]}), True))
        if ESPEC.get(r["id"], ("", None, ""))[2]:
            lst += [(dict(base, **d), v) for d, v in CASOS_ESPECIFICOS.get(r["id"], [])]
        out[r["id"]] = lst
    return out


if __name__ == "__main__":
    main()
