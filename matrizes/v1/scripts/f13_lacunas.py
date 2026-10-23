#!/usr/bin/env python3
"""Fase 13 - texto da minuta: M02.lacunas_mapa (cada marcador e o que o preenche) e M02.tabela_colunas (tabelas
montadas a partir dos itens).

Uso: python3 -I f13_lacunas.py <pasta_Matrizes_v1> <saida_log.txt>

Roda depois do f10_gerar_expr.py (o M02 já tem as colunas _expr). Acrescenta ao M02, logo depois de `lacunas`:

lacunas_mapa (JSON, lista na ordem do texto; uma entrada por marcador da coluna `lacunas`):
  marcador    texto do marcador, igual ao da coluna lacunas;
  ocorrencia  qual ocorrência do marcador no texto_literal (contagem sem sobreposição, da esquerda para a direita);
  fonte       o que preenche: VAR_xxx, WZ_xx, CK_..., itens.<atributo>, ou null;
  acao        PREENCHER (padrão; pode ser omitida), ESCOLHA (fica uma das opções do modelo), OPCIONAL (o trecho entra
              ou sai), TABELA (a tabela é montada pela tabela_colunas), REMOVER (instrução do modelo que sai do texto),
              MANTER (fica como está: linha de assinatura ou campo do fornecedor) ou EQUIPE (fonte null: preenchido à
              mão pela equipe; o motivo está em comentario);
  campo       caminho dentro do valor (TABELA guardada como objeto, ex.: VAR_091 campo "fonte_recursos");
  indice      posição na lista (0 = primeiro elemento); com lista_blocos, o motor ajusta a pontuação final da série
              (';', '; e', '.') e omite o bloco sem elemento (se_vazio = OMITE_BLOCO);
  padrao      (na opção) true quando a opção dá um valor que entra sem ter sido informado (P37); listado no log;
  alternativas  outras fontes, em ordem, usadas quando a fonte está vazia;
  inicial_minuscula / inicial_maiuscula  ajuste da primeira letra do valor (opção do checklist no meio ou no início da
              frase);
  filtro_item JSON Logic avaliado em cada item (formato NUMEROS_DOS_ITENS);
  formato     TEXTO (padrão), NUMERO_EXTENSO ("30 (trinta)"), PERCENTUAL_EXTENSO ("5% (cinco por cento)"),
              PERCENTUAL_2 ("25,00%"), MOEDA ("R$ 1.234,56"), MOEDA_POR_EXTENSO ("(mil duzentos e trinta e quatro
              reais e cinquenta e seis centavos)"), DATA ("DD/MM/AAAA"), DIA, MES_EXTENSO, ANO, LISTA_TEXTO
              ("a, b e c"), LISTA_LINHAS (uma por linha), MINUSCULA (código em minúsculas), INICIAL_MINUSCULA (opção do
              checklist no meio da frase: 'Dois terços' -> 'dois terços'), ITEM ("item 2"), POR_ITEM
              ("item 1: valor; item 3: valor", da lista de itens), NUMEROS_DOS_ITENS ("1, 3 e 5": itens com o atributo
              preenchido ou com filtro_item verdadeiro);
  M08.lacunas_mapa (Fase 14): mesmo formato; marcador = trecho entre colchetes de primeiro nível do texto_proposto.
  unidade     VAR com a unidade do número (DIAS, MESES ou ANOS), escrita depois dele, no singular quando o número é 1;
  texto       modelo da saída com {valor} (valor já formatado); padrão "{valor}";
  opcoes      [{"quando": JSON Logic, "texto": modelo}]: vale a primeira verdadeira; nenhuma verdadeira = lacuna;
  grupo       marcadores do mesmo grupo formam um trecho só (do primeiro ao último, com os " OU " do modelo no meio),
              trocado pela primeira opção verdadeira do grupo; estende_desde e estende_ate incluem no trecho o texto
              fixo imediatamente antes do primeiro marcador ou depois do último;
  quando      (OPCIONAL) JSON Logic: verdadeira = o trecho entra, sem os colchetes ou com o texto/valor; falsa = sai,
              junto com remove_antes (texto imediatamente antes do marcador), e no lugar fica se_falso (padrão: nada);
  se_vazio    LACUNA (padrão) ou OMITE_BLOCO;
  comentario  por que a fonte é null, ou como o marcador é tratado.
Valor ausente sempre vira lacuna marcada; o motor não inventa valor.

tabela_colunas (JSON, só nas tabelas que vêm dos itens): linhas, filtro, colunas (cabeçalho do modelo e o que preenche),
orçamento sigiloso (NE-004) e a linha de cota reservada.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv, ler_csv  # noqa: E402
from jlogic import e, eq, inn, ne, tem, var  # noqa: E402

FONTE = ("Fase 13 (23/10/2026): lacunas_mapa e tabela_colunas INFERIDOS pelo f13_lacunas.py a partir do texto_literal, "
         "da coluna lacunas, do M05 (usada_em) e do M04; achado do Marco 1 (ligação só pelo usada_em em 50 de 106 "
         "blocos).")


def P(m, fonte, **kw):
    return dict(marcador=m, fonte=fonte, **kw)


def EQUIPE(m, motivo):
    return dict(marcador=m, fonte=None, acao="EQUIPE", comentario=motivo)


def TAB(m):
    return dict(marcador=m, fonte=None, acao="TABELA",
                comentario="marcador da tabela do modelo: a tabela é montada pela coluna tabela_colunas")


def REM(m, motivo):
    return dict(marcador=m, fonte=None, acao="REMOVER", comentario=motivo)


def MANTER(m, motivo):
    return dict(marcador=m, fonte=None, acao="MANTER", comentario=motivo)


def OP(m, fonte, grupo, opcoes, **kw):
    return dict(marcador=m, fonte=fonte, acao="ESCOLHA", grupo=grupo, opcoes=opcoes, **kw)


def OPC(m, fonte, quando, **kw):
    return dict(marcador=m, fonte=fonte, acao="OPCIONAL", quando=quando, **kw)


def o(quando, texto):
    return {"quando": quando, "texto": texto}


def lista(m, fonte, i, blocos, **kw):
    d = dict(marcador=m, fonte=fonte, indice=i, lista_blocos=blocos, **kw)
    if i > 0:
        d["se_vazio"] = "OMITE_BLOCO"
    if i == len(blocos) - 1:
        d["juntar_restante"] = True
        d["comentario"] = (d.get("comentario", "") + " Último bloco da série: elementos a partir deste juntam-se com '; '."
                           ).strip()
    return d


EXT = "NUMERO_EXTENSO"
PEXT = "PERCENTUAL_EXTENSO"
MARCAS = "fica com a equipe"
NORMA = ("cita norma (lei, decreto, artigo ou resolução) que precisa estar na base normativa conferida (M07); o sistema "
         "não escreve número de norma sem conferência")
FORNECEDOR = "campo preenchido pelo fornecedor na declaração (Anexo II); fica em branco na minuta"


def serie(bloco_base, n, fonte, **kw):
    blocos = [f"{bloco_base}.{k}" for k in range(1, n + 1)]
    return {b: [lista("[...]", fonte, i, blocos, **kw)] for i, b in enumerate(blocos)}


M = {
    "TR-CAB.03": [P("ÓRGÃO OU ENTIDADE PÚBLICA", "VAR_004", formato="LISTA_LINHAS",
                    comentario="linhas do cabeçalho do órgão, do perfil da OM")],
    "TR-CAB.04": [P("xxxxx.xxxxxx/xxxx-xx", "VAR_001")],
    "TR-1.1": [P("[INSERIR OBJETO]", "VAR_008"),
               OPC("[incluindo instalação, montagem INCLUIR ATIVIDADES]", "VAR_009", eq("WZ_08", "SIM"),
                   formato="LISTA_TEXTO", texto="incluindo {valor}", remove_antes=", ",
                   comentario="entra só com atividades além da entrega (WZ-08 = SIM); sem elas sai junto com a vírgula")],
    "TR-1.1.TAB1": [TAB("R$ ...."), TAB("R$ ...."), TAB("XX,XX%")],
    "TR-1.5": [P("[indicar o prazo]", "VAR_034", formato=EXT, unidade="VAR_163"),
               P("[indicar o termo inicial da vigência]", "VAR_035")],
    "TR-1.6": [P("[indicar o prazo, limitado a 5 anos]", "VAR_034", formato=EXT, unidade="VAR_163"),
               P("[indicar o termo inicial da vigência]", "VAR_035")],
    "TR-1.7": [P("[...]", "VAR_036", comentario="por que o fornecimento é contínuo (fatos do checklist)"),
               OP("[...]", "VAR_036", "base_vantagem", []),
               OP("[o Estudo Técnico Preliminar]", None, "base_vantagem",
                  [dict(o(True, "o Estudo Técnico Preliminar"), padrao=True)],
                  comentario="padrão aceito na P37: o sistema gera o ETP do processo; a equipe troca na revisão se "
                             "preferir texto próprio ou nota técnica"),
               OP("[os termos da Nota Técnica .../...]", None, "base_vantagem", [],
                  comentario="o sistema gera o ETP do processo, então a vantagem da vigência plurianual remete a ele; "
                             "texto próprio ou nota técnica são trocados pela equipe na revisão; aceito na P37")],
    "TR-1.8": [P("[indicar o prazo, limitado a um ano da ocorrência da emergência ou calamidade]", "VAR_034",
                 formato=EXT, unidade="VAR_163"),
               P("[indicar o termo inicial da vigência]", "VAR_035")],
    "TR-2.2": [P("[ANO]", "VAR_038")],
    "TR-2.2.I": [P("[...]", "VAR_039")],
    "TR-2.2.II": [P("[...]", "VAR_040", formato="DATA")],
    "TR-2.2.III": [P("[...]", "VAR_041")],
    "TR-2.2.IV": [P("[...]", "VAR_042")],
    "TR-2.2.V": [P("[...]", "VAR_043")],
    "TR-2.3": [P("[ANO]", "VAR_038")],
    **serie("TR-4.1", 3, "VAR_044"),
    "TR-4.2": [P("(...)", "itens.marca_indicada", formato="POR_ITEM",
                 comentario="marca ou modelo indicado em cada item (VAR-115); a justificativa fica no ETP (VAR-046)")],
    "TR-4.3": [P("xxxxx.xxxxxx/xxxx-xx", "VAR_047")],
    **{b: [lista("[...]", "VAR_048", i, ["TR-4.3.1.1", "TR-4.3.1.2"])]
       for i, b in enumerate(["TR-4.3.1.1", "TR-4.3.1.2"])},
    **serie("TR-4.5", 3, "VAR_049", formato="ITEM"),
    "TR-4.6": [P("[indicar o endereço]", "VAR_166"), P("[indicar o prazo]", "VAR_167")],
    **{b: [lista("(....)", "VAR_051", i, ["TR-4.9.1", "TR-4.9.2"], campo="itens"),
           lista("." * (11 + i), "VAR_051", i, ["TR-4.9.1", "TR-4.9.2"], campo="criterios")]
       for i, b in enumerate(["TR-4.9.1", "TR-4.9.2"])},
    "TR-4.13": [P("XX (xxxxx)", "VAR_052", formato=EXT)],
    "TR-4.17": [P("XX% (xxxxx por cento)", "VAR_053", formato=PEXT)],
    **serie("TR-4.18", 3, "VAR_164"),
    **serie("TR-4.19", 3, "VAR_165"),
    "TR-NE016.02": [EQUIPE("XX% (xxxxx por cento)", "texto da nota 3 da NE-016, fora do corpo do modelo: o sistema não o "
                                                    "gera e, se usado, é redigido à mão (validação do M03, NE-016)"),
                    EQUIPE("XX% (xxxxx por cento)", "idem: percentual máximo da subcontratação de ME/EPP (NE-016 nota 3)")],
    "TR-NE016.03": [EQUIPE("[...]", "parcela do objeto da subcontratação de ME/EPP (NE-016 nota 3), redigida à mão")],
    "TR-NE016.04": [EQUIPE("[...]", "parcela do objeto da subcontratação de ME/EPP (NE-016 nota 3), redigida à mão")],
    "TR-4.25": [P("XX% (xxxxx por cento)", "VAR_055", formato=PEXT),
                OP("[total]", "VAR_056", "base_garantia", [o(eq("VAR_056", "TOTAL"), "total")]),
                OP("[anual]", "VAR_056", "base_garantia", [o(eq("VAR_056", "ANUAL"), "anual")])],
    "TR-4.42": [EQUIPE(m, "margem de preferência: " + NORMA + "; tipo, percentual e enquadramento vêm da mesma "
                                                          "resolução, preenchidos à mão (VAR-058)")
                for m in (".............", "[normal]", "[adicional]", "........", ".....................",
                          ".........................", "................",
                          "[bens manufaturados nacionais que atendam a normas técnicas brasileiras]",
                          "[bens reciclados, recicláveis ou biodegradáveis]")],
    "TR-5.1": [P(".........", "VAR_060", formato=EXT), P("................................", "VAR_061")],
    "TR-5.2.TAB1": [TAB("[...]") for _ in range(5)],
    "TR-5.3": [P("(...)", "VAR_063", formato=EXT)],
    "TR-5.4": [P("[...]", "VAR_064", comentario="endereços, horários e setores (perfil da OM, WZ-28, CK-X-01 ou CK-P-9.1); "
                                                "várias entradas juntam-se com '; '")],
    "TR-5.4.1": [OP("...... (......)", "VAR_065", "validade",
                    [o(e(tem("VAR_065"), {"!": [inn("prazo total", var("VAR_065"))]}), "{valor}")],
                    formato="INICIAL_MINUSCULA"),
                 OP("(dias ou meses ou anos)", "VAR_065", "validade", []),
                 OP("(metade, um terço, dois terços etc.)", "VAR_065", "validade",
                    [o(inn("prazo total", var("VAR_065")), "{valor} recomendado pelo fabricante")],
                    formato="INICIAL_MINUSCULA",
                    estende_ate=" do prazo total recomendado pelo fabricante",
                    comentario="a VAR-065 guarda o critério comum aos perecíveis como texto da opção do checklist "
                               "('12 meses' ou '75% do prazo total'); o trecho do modelo fica com a forma que corresponde "
                               "ao critério. Sem critério comum (VAR-065 vazia), a validade vai na tabela do item 1.1 e o "
                               "bloco fica com lacuna para a equipe remeter à tabela")],
    "TR-5.6": [P("___ (____)", "VAR_066", formato=EXT)],
    "TR-5.12": [P("XX (xxxxx)", "VAR_067", formato=EXT)],
    **serie("TR-6.15", 3, "VAR_068"),
    "TR-7.2.4.1": [P("XX% (xxxxx por cento)", "VAR_069", formato=PEXT), P("XX (xxxxx)", "VAR_070", formato=EXT)],
    "TR-7.2.4.3": [P("XX% (xxxxx por cento)", "VAR_071", campo="e_a_h.minimo", formato=PEXT),
                   P("XX% (xxxxx por cento)", "VAR_071", campo="e_a_h.maximo", formato=PEXT)],
    "TR-7.2.4.4": [P("XX% (xxxxx por cento)", "VAR_071", campo="c.minimo", formato=PEXT),
                   P("XX% (xxxxx por cento)", "VAR_071", campo="c.maximo", formato=PEXT)],
    "TR-7.2.4.5": [P("XX% (xxxxx por cento)", "VAR_071", campo="b.minimo", formato=PEXT),
                   P("XX% (xxxxx por cento)", "VAR_071", campo="b.maximo", formato=PEXT)],
    "TR-7.2.4.6": [P("XX% (xxxxx por cento)", "VAR_071", campo="d.minimo", formato=PEXT),
                   P("XX% (xxxxx por cento)", "VAR_071", campo="d.maximo", formato=PEXT)],
    "TR-7.2.4.7": [P("XX% (xxxxx por cento)", "VAR_071", campo="a.minimo", formato=PEXT),
                   P("XX% (xxxxx por cento)", "VAR_071", campo="a.maximo", formato=PEXT),
                   OPC("[, ressalvadas as seguintes infrações também enquadráveis nessa alínea:]", "WZ_33",
                       eq("WZ_33", "SIM"), remove_antes=" ", se_falso=".",
                       comentario="entra só com infrações de penalidade própria (WZ-33 = SIM); sem elas, a alínea termina "
                                  "com ponto, como as demais (TR-7.2.4.3 a TR-7.2.4.6)")],
    "TR-7.2.4.7.1": [P("[INDICAR ITENS ESPECÍFICOS DE INEXECUÇÃO PARCIAL QUE JUSTIFIQUEM PENALIDADE DIVERSA]", "VAR_072",
                       comentario="infrações da VAR-072, juntas com '; '")],
    "TR-7.7": [P("XX (xxxxx)", "VAR_073", formato=EXT)],
    "TR-8.2": [P(".... (...)", "VAR_074", formato=EXT)],
    "TR-8.3": [P("XXXX(XXXX)", "VAR_075", formato=EXT)],
    "TR-8.4": [P("XXXXX (XXX)", "VAR_076", formato=EXT)],
    "TR-8.21": [P("XXXX", "VAR_077")],
    "TR-8.27": [P("......... (parcial/total)", "VAR_079", campo="forma", formato="MINUSCULA")],
    "TR-8.28": [P("R$ ......", "VAR_079", campo="valor", formato="MOEDA"),
                P("(valor por extenso)", "VAR_079", campo="valor", formato="MOEDA_POR_EXTENSO"),
                P("(incluir condicionante – ex: seja assinado o termo de contrato, ou seja, prestada a garantia etc.)",
                  "VAR_079", campo="condicionante", estende_desde="... ",
                  comentario="o '... ' antes do marcador faz parte da lacuna do modelo")],
    "TR-8.29.1": [P("R$.....", "VAR_079", campo="valor_segunda_etapa", formato="MOEDA"),
                  P("(valor em extenso)", "VAR_079", campo="valor_segunda_etapa", formato="MOEDA_POR_EXTENSO")],
    "TR-8.29.2": [P("(...)", "VAR_079", campo="etapas_seguintes")],
    "TR-8.32": [P("........ (especificar o índice de correção monetária a ser adotado)", "VAR_079",
                  campo="indice_correcao")],
    "TR-8.34": [P("..... (....)", "VAR_079", campo="prazo_dias", formato=EXT),
                P("...... (recibo OU nota fiscal OU fatura OU documento idôneo)", "VAR_079", campo="documento")],
    "TR-8.36.2": [P("...%", "VAR_079", campo="garantia_adicional_percentual", texto="{valor}%")],
    "TR-8.40": [P("__/__/__", "VAR_015", formato="DATA"),
                ],
    "TR-8.41": [P("___________", "VAR_078"),
                REM("(indicar o índice a ser adotado)", "instrução do modelo; sai junto com o espaço anterior")],
    "TR-9.1": [OP("[PREGÃO]", "WZ_02", "modalidade", [o(eq("WZ_02", "PREGAO"), "PREGÃO")]),
               OP("[CONCORRÊNCIA]", "WZ_02", "modalidade", [o(eq("WZ_02", "CONCORRENCIA"), "CONCORRÊNCIA")]),
               OP("[MENOR PREÇO]", "WZ_03", "criterio", [o(eq("WZ_03", "MENOR_PRECO"), "MENOR PREÇO")]),
               OP("[MAIOR DESCONTO]", "WZ_03", "criterio", [o(eq("WZ_03", "MAIOR_DESCONTO"), "MAIOR DESCONTO")]),
               OP("[TÉCNICA E PREÇO]", "WZ_03", "criterio", [o(eq("WZ_03", "TECNICA_E_PRECO"), "TÉCNICA E PREÇO")])],
    "TR-9.2": [OP("[74 OU 75]", "WZ_04", "artigo",
                  [o(eq("WZ_04", "ART74_INEXIGIBILIDADE"), "74"),
                   o(inn(var("WZ_04"), ["ART75_II_VALOR", "ART75_VIII_EMERGENCIA", "ART75_OUTRO_INCISO"]), "75")],
                  comentario="artigo pela opção da WZ-04 (texto do próprio marcador do modelo)"),
               OP("[indicar o inciso]", "WZ_04", "inciso",
                  [o(eq("WZ_04", "ART75_II_VALOR"), "II"), o(eq("WZ_04", "ART75_VIII_EMERGENCIA"), "VIII")],
                  comentario="inciso pela opção da WZ-04 quando ela o diz (II e VIII, nomes das próprias opções); "
                             "inexigibilidade e 'outro inciso' ficam com a equipe, com a VAR-023"),
               P("[descrever a fundamentação da contratação para enquadramento no dispositivo legal indicado]", "VAR_024")],
    "TR-9.3": [P("............", "VAR_111", formato="MINUSCULA",
                 comentario="INTEGRAL, PARCELADO ou CONTINUADO, em minúsculas, como as opções do modelo"),
               REM("[integral/parcelado/continuado]", "opções do modelo; saem com o valor escrito")],
    "TR-9.4.1": [OP("XXXXXX", "VAR_032", "local_tabela",
                    [o(eq("VAR_032", "PLANILHA_ANEXA"), "planilha de composição de preços anexa ao edital"),
                     o(eq("VAR_032", "ITEM_DO_TR"), "tabela constante no item 1.1")],
                    estende_desde="planilha de composição de preços anexa ao edital OU tabela constante no item ",
                    comentario="o 'OU' do modelo está fora de colchetes: o trecho inteiro vira a opção escolhida; a "
                               "tabela de preços unitários do TR é a do item 1.1 (TR-1.1.TAB1)")],
    "TR-9.14": [EQUIPE("............ (especificar a atividade contratada sujeita à autorização)",
                       "a SET-08 preenche este bloco (PREENCHE_BLOCO) com a atividade da VAR-136; sem a SET-08, equipe"),
                EQUIPE("....... (especificar o órgão competente)",
                       "a SET-08 preenche este bloco com o órgão da VAR-136; sem a SET-08, equipe"),
                EQUIPE(".....", "artigo da norma: " + NORMA),
                EQUIPE("........", "número da norma: " + NORMA)],
    "TR-9.26": [OP("...................", "WZ_54", "exercicios", []),
                OP("[do último exercício social]", "WZ_54", "exercicios",
                   [o(eq("WZ_54", "ULTIMO_EXERCICIO"), "do último exercício social")]),
                OP("[dos dois últimos exercícios sociais]", "WZ_54", "exercicios",
                   [o(eq("WZ_54", "DOIS_ULTIMOS_EXERCICIOS"), "dos dois últimos exercícios sociais")],
                   comentario="os pontos antes das opções fazem parte da escolha e saem com ela")],
    "TR-9.27": [OP("[capital mínimo]", "VAR_081", "capital_ou_pl", [o(eq("VAR_081", "CAPITAL_MINIMO"), "capital mínimo")]),
                OP("[patrimônio líquido mínimo]", "VAR_081", "capital_ou_pl",
                   [o(eq("VAR_081", "PATRIMONIO_LIQUIDO_MINIMO"), "patrimônio líquido mínimo")]),
                P("......", "VAR_082"),
                REM("[até 10%]", "limite do modelo (instrução); sai junto com o espaço anterior"),
                OP("[valor total estimado da contratação]", "VAR_083", "base_qualif",
                   [o(eq("VAR_083", "VALOR_TOTAL"), "valor total estimado da contratação")]),
                OP("[valor total estimado da parcela pertinente]", "VAR_083", "base_qualif",
                   [o(eq("VAR_083", "VALOR_DA_PARCELA"), "valor total estimado da parcela pertinente")])],
    "TR-9.33": [P(".........(escrever por extenso, se for o caso)", "VAR_084")],
    **serie("TR-9.34.1", 3, "VAR_085"),
    "TR-NE071.01": [P("....", "VAR_165", formato="LISTA_TEXTO",
                      comentario="parcelas cuja subcontratação foi autorizada (VAR-165)")],
    "TR-9.35": [EQUIPE("........", "a SET-06 preenche este bloco (PREENCHE_BLOCO) com a Autorização Especial dos itens "
                                   "da VAR-123; outro requisito de lei especial, equipe"),
                EQUIPE("............", "lei especial: " + NORMA)],
    "TR-10.1": [P("R$...", "VAR_014", formato="MOEDA"), P("(por extenso)", "VAR_014", formato="MOEDA_POR_EXTENSO"),
                OP("[tabela contida no item 1.1 acima]", "VAR_089", "local_valor",
                   [o(eq("VAR_089", "ITEM_1.1"), "tabela contida no item 1.1 acima")]),
                OP("[em anexo]", "VAR_089", "local_valor", [o(eq("VAR_089", "ANEXO"), "em anexo")])],
    "TR-10.2": [P("R$.....", "VAR_016", formato="MOEDA")],
    "TR-11.2.I": [P("[...]", "VAR_091", campo="gestao_unidade")],
    "TR-11.2.II": [P("[...]", "VAR_091", campo="fonte_recursos")],
    "TR-11.2.III": [P("[...]", "VAR_091", campo="programa_trabalho")],
    "TR-11.2.IV": [P("[...]", "VAR_091", campo="elemento_despesa")],
    "TR-11.2.V": [P("[...]", "VAR_091", campo="plano_interno")],
    "TR-12.1": [OPC("[exceto o custo estimado da contratação, que possui caráter sigiloso até o julgamento das propostas]",
                    "WZ_40", eq("WZ_40", "SIM"), remove_antes=" ",
                    comentario="entra só com orçamento sigiloso (WZ-40 = SIM)")],
    "TR-ASSIN.01": [P("[Local]", "VAR_005"), P("[dia]", "VAR_097", formato="DIA"),
                    P("[mês]", "VAR_097", formato="MES_EXTENSO"), P("[ano]", "VAR_097", formato="ANO")],
    "TR-ASSIN.02": [MANTER("__________________________________", "linha de assinatura")],
    "TR-AI-1.1": [P("...............", "VAR_170"),
                  OP("............", "VAR_171", "instrumento", []),
                  OP("[Nota de Empenho/Carta Contrato/Autorização]", "VAR_171", "instrumento",
                     [o(eq("VAR_171", "NOTA_DE_EMPENHO"), "Nota de Empenho"),
                      o(eq("VAR_171", "CARTA_CONTRATO"), "Carta Contrato"),
                      o(eq("VAR_171", "AUTORIZACAO"), "Autorização")]),
                  OP("[constante deste Anexo]", "VAR_171", "instrumento",
                     [o(eq("VAR_171", "ESTE_ANEXO"), "constante deste Anexo")])],
    "TR-AI-1.3.2": [OP("Edital OU na Autorização de Contratação Direta e/ou no Aviso de Dispensa Eletrônica", "WZ_01",
                       "instrumento_convocatorio",
                       [o(eq("WZ_01", "LICITACAO"), "no Edital"),
                        o(eq("WZ_01", "CONTRATACAO_DIRETA"),
                          "na Autorização de Contratação Direta e/ou no Aviso de Dispensa Eletrônica")],
                       estende_desde="no ")],
    "TR-AI-2.8": [P("..............................(máximo de um ano)", "VAR_034", formato=EXT, unidade="VAR_163"),
                  P("............................. (data da ocorrência da emergência ou da calamidade)", "VAR_035")],
    "TR-AI-3.1.8.1": [OP("XXXXXXX", "VAR_094", "prazo_decisao",
                         [o(tem("VAR_094"), "{valor}"), dict(o(True, "1 (um) mês"), padrao=True)],
                         comentario="sem prazo informado vale um mês (NE-087; art. 123, parágrafo único, da Lei nº "
                                    "14.133, de 2021, citado na nota); aceito na P37")],
    "TR-AI-3.1.9": [P("XXXXXX", "VAR_095")],
    "TR-AI-4.1.1": [OPC("e da relação da rede de assistência técnica autorizada", "WZ_43",
                        eq("WZ_43", "SUBSTITUTIVO_PEQUENO_VALOR"), remove_antes=", ",
                        comentario="só no instrumento substitutivo do art. 95, I (NE-092, condicao_inclusao do bloco)")],
    "TR-AI-8.1": [P("......", "VAR_168"), P("......", "VAR_169")],
    "TR-AII.03": [MANTER("..................... (identificar o Contratado)", FORNECEDOR),
                  OP("Edital OU Aviso de Contratação Direta", "WZ_01", "instrumento_anexo2",
                     [o(eq("WZ_01", "LICITACAO"), "Edital"),
                      o(eq("WZ_01", "CONTRATACAO_DIRETA"), "Aviso de Contratação Direta")]),
                  EQUIPE("...........", "número do certame: só existe com a publicação; a equipe preenche na fase "
                                        "externa"),
                  EQUIPE(".......", "ano do certame: idem")],
    "TR-AII.04": [MANTER("........", FORNECEDOR), MANTER("...................", FORNECEDOR), MANTER("....", FORNECEDOR)],
    "TR-AII.05": [MANTER("__________________________________________", "linha de assinatura do fornecedor")],
    "TR-AII.06": [MANTER("(Nome e Cargo do Representante Legal)", FORNECEDOR)],
}

# -------------------------------------------------------------------- tabelas montadas a partir dos itens
COTA = e(eq("tratamento_me_epp", "COTA"), {">": [var("quantidade_cota"), 0]})
SIGILOSO = eq("WZ_40", "SIM")
TABELAS = {
    "TR-1.1.TAB1": {
        "linhas": "itens", "ordem": "numero",
        "numeracao": "ITENS_E_COTAS_NO_FIM (P35, decisão do dono do projeto, 23/10/2026): cada item de ampla "
                     "participação fica com o próprio número (VAR-156), sem renumeração; as linhas de cota vão todas "
                     "para o fim da tabela, depois do último item, na ordem dos itens de origem, e recebem os números "
                     "seguintes ao maior número de item (ex.: itens 1 a 5, cotas 6 e 7). As referências a número de item "
                     "no TR (amostras, padrões) continuam com o número do item.",
        "colunas": [
            {"cabecalho": "ITEM", "fonte": "itens.numero", "comentario": "número do item (VAR-156), sem renumerar"},
            {"cabecalho": "ESPECIFICAÇÃO", "fonte": "itens.especificacao",
             "complementos": [
                 {"fonte": "itens.marca_indicada", "rotulo": "Marca ou modelo de referência"},
                 {"fonte": "itens.compatibilidade", "rotulo": "Compatibilidade"},
                 {"fonte": "itens.faixa_temperatura", "rotulo": "Faixa de temperatura"},
                 {"fonte": "itens.validade_minima", "rotulo": "Validade mínima na entrega",
                  "quando": {"!": [var("VAR_065")]},
                  "comentario": "só quando os perecíveis não têm critério comum (VAR-065 vazia; condicao_inclusao do "
                                "TR-5.4.1)"},
                 {"fonte": "itens.garantia_minima_meses", "rotulo": "Garantia mínima", "texto": "{valor} meses"}],
             "comentario": "complementos em linhas abaixo da especificação, com o rótulo, só quando o atributo tem valor "
                           "(NE-003 nota 1: a tabela é ilustrativa)"},
            {"cabecalho": "CATMAT", "fonte": "itens.catmat"},
            {"cabecalho": "UNIDADE DE MEDIDA", "fonte": "itens.unidade_medida"},
            {"cabecalho": "QUANTIDADE", "fonte": "itens.quantidade_principal", "formato": "NUMERO"},
            {"cabecalho": "VALOR UNITÁRIO", "fonte": "itens.valor_unitario", "formato": "MOEDA", "sigiloso": "SIGILOSO"},
            {"cabecalho": "VALOR TOTAL", "fonte": "itens.valor_total", "formato": "MOEDA", "sigiloso": "SIGILOSO"}],
        "orcamento_sigiloso": {"quando": SIGILOSO, "colunas": ["VALOR UNITÁRIO", "VALOR TOTAL"], "texto": "SIGILOSO",
                               "base": "NE-004: com orçamento sigiloso não se preenchem valor unitário e valor total; "
                                       "a célula traz a opção 'SIGILOSO' do próprio modelo"},
        "linha_cota": {
            "quando": COTA,
            "posicao": "FIM_DA_TABELA: depois do último item de ampla participação, na ordem dos itens de origem",
            "numero": "maior número de item + 1, + 2... (uma linha de cota por item com cota)",
            "valores": {"ITEM": "numero da linha de cota",
                        "ESPECIFICAÇÃO": "Cota reservada para ME/EPP do item {itens.numero do item de origem}",
                        "CATMAT": "itens.catmat", "UNIDADE DE MEDIDA": "itens.unidade_medida",
                        "QUANTIDADE": "itens.quantidade_cota", "VALOR UNITÁRIO": "itens.valor_unitario",
                        "VALOR TOTAL": "itens.valor_total_cota"},
            "regra": "entra para cada item com tratamento COTA (VAR-113) e quantidade reservada maior que zero (VAR-118); "
                     "a linha de origem fica com a quantidade principal (VAR-174 = quantidade menos a cota) e a da cota "
                     "com a VAR-118. A célula cita o item de origem (P35), no lugar do 'Idem ao Item 1 – ... XX,XX%' do "
                     "modelo; o percentual da cota está no TR-4.41. Item sem cota não tem linha de cota; cota zero fica "
                     "em ampla (VAL-051)",
            "base": "TR-1.1.TAB1 do modelo (linha 'Idem ao Item 1 – Cota reservada'); P35 (decisão 0008); NE-022; "
                    "VAR-113, VAR-118"},
        "sem_itens": "lacuna: a tabela não é montada sem a lista de itens",
    },
}
for k, papel, titulo in (("TR-1.1.1.TAB1", "GERENCIADOR", "Órgão Gerenciador: {orgao}"),
                         ("TR-1.1.1.TAB2", "PARTICIPANTE", "Órgão Participante: {orgao}"),
                         ("TR-1.1.1.TAB3", "PARTICIPANTE", "Órgão Participante: {orgao}")):
    TABELAS[k] = {
        "linhas": "VAR_029", "filtro": eq("papel", papel),
        "uma_tabela_por": "orgao" if papel == "PARTICIPANTE" else None,
        "qual": {"TR-1.1.1.TAB1": "o gerenciador", "TR-1.1.1.TAB2": "o 1º participante",
                 "TR-1.1.1.TAB3": "o 2º participante e, repetida, cada participante seguinte"}[k],
        "titulo": titulo,
        "colunas": [
            {"cabecalho": "item" if k.endswith("TAB1") else "Item", "campo": "item"},  # como no modelo
            {"cabecalho": "DESCRIÇÃO/ ESPECIF.", "fonte": "itens.especificacao", "ligacao": "campo item = itens.numero"},
            {"cabecalho": "UNIDADE / DE / MEDIDA", "fonte": "itens.unidade_medida", "ligacao": "campo item = itens.numero"},
            {"cabecalho": "REQUISIÇÃO / MÍNIMA", "campo": "minima", "formato": "NUMERO"},
            {"cabecalho": "REQUISIÇÃO / Máxima", "campo": "maxima", "formato": "NUMERO"},
            {"cabecalho": "Quantidade / total", "campo": "total", "formato": "NUMERO"}],
        "estrutura_da_fonte": "VAR-029: uma linha por órgão e item, com orgao, papel (GERENCIADOR ou PARTICIPANTE), item, "
                              "minima, maxima e total (VAR-029.validacao: mínima até máxima; total igual à soma)",
        "sem_linhas": "lacuna: a tabela não é montada sem as quantidades da IRP",
    }
TABELAS["TR-5.2.TAB1"] = {
    "linhas": "VAR_062", "ordem": "parcela",
    "colunas": [
        {"cabecalho": "Parcela", "campo": "parcela", "formato": "ORDINAL", "comentario": "1ª, 2ª, 3ª..."},
        {"cabecalho": "Composição da parcela", "campo": "composicao",
         "comentario": "lista de {item, quantidade} vira '{quantidade} unidades do item {item}', separadas por ', ', como "
                       "no modelo; texto livre entra como está"},
        {"cabecalho": "Prazo de entrega", "texto": "{prazo_dias} dias da {termo_inicial}",
         "comentario": "termo inicial: Assinatura, Ordem de Fornecimento ou outro informado (opções do modelo)"}],
    "estrutura_da_fonte": "VAR-062: uma linha por parcela, com parcela (número), composicao, prazo_dias e termo_inicial; "
                          "o complemento CK-X-02 traz texto livre, que não monta a tabela e fica como lacuna para a equipe",
    "sem_linhas": "lacuna",
}


# -------------------------------------------------------------------- M08 (Fase 14, P36): mapa das cláusulas
# Marcador do M08 = trecho entre colchetes de primeiro nível do texto_proposto (o de dentro, como o [VAR-143] da SET-17,
# é tratado no texto do de fora). A cláusula não é reescrita: o mapa diz o que preenche cada marcador. Quando a mesma VAR
# aparece em vários marcadores, cada um vai para a pergunta do checklist que dá aquela parte; o que nenhuma pergunta
# dá fica com a equipe. Cada entrada: (trecho que o marcador contém, para conferir, entrada do mapa sem 'marcador').
def M8(confere, d):
    return (confere, d)


TEXTO_UNICO = ("a VAR-{v} chega como um texto só (caixa de resposta do checklist), sem separar esta parte; o texto entra "
               "inteiro no marcador de {onde}")
M08_MAPA = {
    "SET-01": [M8("itens que dependem", dict(fonte="VAR_125", campo="itens")),
               M8("quantidade e descrição", dict(fonte="VAR_125", campo="equipamento")),
               M8("VAR-126", dict(fonte="VAR_126", formato="LISTA_TEXTO")),
               M8("VAR-127", dict(fonte="VAR_127"))],
    "SET-02": [M8("itens e cuidados", dict(fonte="itens.faixa_temperatura", formato="NUMEROS_DOS_ITENS",
                                           comentario="itens com faixa de temperatura (VAR-122); os cuidados de "
                                                      "permanentes (VAR-128) entram no trecho 'Para permanentes'")),
               M8("[VAR-122]", dict(fonte="itens.faixa_temperatura", formato="POR_ITEM")),
               M8("registro contínuo", dict(fonte="CK_C_13_2", acao="OPCIONAL", quando=eq("CK_C_13_2", "Sim"),
                                            texto="e com registro contínuo da temperatura durante o transporte, "
                                                  "apresentado no ato da entrega", remove_antes=" ",
                                            comentario="trecho do próprio marcador, sem a remissão '(VAR-129)'; entra com "
                                                       "a CK-C-13.2 = Sim")),
               M8("Para permanentes", dict(fonte="VAR_128", acao="OPCIONAL", quando=tem("VAR_128"),
                                           texto="O Contratado providenciará a logística especial de transporte e "
                                                 "movimentação descrita a seguir: {valor}.", remove_antes=" ",
                                           comentario="trecho do próprio marcador; a remissão 'descrita em VAR-128' vira o "
                                                      "texto da VAR-128 (CK-P-8.7 ou CK-C-13.3)"))],
    "SET-03": [M8("VAR-130: itens", dict(fonte=None, acao="EQUIPE",
                                         comentario=TEXTO_UNICO.format(v="130", onde="documentos"))),
               M8("documentos exigidos", dict(fonte="VAR_130", comentario="CK-C-13.4 e caixa da CK-C-15.4"))],
    "SET-04": [M8("VAR-133", dict(fonte="VAR_133")),
               M8("VAR-134", dict(fonte=None, acao="REMOVER",
                                  comentario="a VAR-134 não recebe mais a resposta Sim/Não (Fase 13); o compromisso de "
                                             "substituição já está no texto da cláusula"))],
    "SET-06": [M8("itens com controle especial", dict(fonte="itens.controle_especial", formato="NUMEROS_DOS_ITENS",
                                                      filtro_item=eq("controle_especial", "S")))],
    "SET-07": [M8("VAR-135: itens", dict(fonte=None, acao="EQUIPE",
                                         comentario=TEXTO_UNICO.format(v="135", onde="requisitos"))),
               M8("na proposta ou na entrega", dict(fonte=None, acao="EQUIPE",
                                                    comentario="escolha da equipe: o checklist não diz quando a "
                                                               "comprovação é exigida")),
               M8("requisito por item", dict(fonte="VAR_135"))],
    "SET-08": [M8("distribuição ou comércio", dict(fonte=None, acao="EQUIPE",
                                                   comentario="a VAR-136 traz as autorizações exigidas (licença "
                                                              "sanitária, AFE, AE), não a atividade")),
               M8("vigilância sanitária ou Anvisa", dict(fonte=None, acao="EQUIPE",
                                                         comentario="o órgão expedidor depende da autorização; a "
                                                                    "VAR-136 não o separa"))],
    "SET-09": [M8("setor de recebimento", dict(fonte=None, acao="EQUIPE",
                                               comentario="o setor de recebimento vem com o endereço de entrega (VAR-064, "
                                                          "TR-5.4); o checklist não o separa")),
               M8("[VAR-131]", dict(fonte=None, acao="EQUIPE",
                                    comentario="antecedência do agendamento: o checklist só pergunta se há agendamento "
                                               "(CK-C-12.6, CK-P-8.5)")),
               M8("horário, veículo", dict(fonte="VAR_131", comentario="caixa da CK-C-12.7 ou da CK-P-8.6"))],
    "SET-10": [M8("VAR-132: itens", dict(fonte=None, acao="EQUIPE",
                                         comentario=TEXTO_UNICO.format(v="132", onde="prazo"))),
               M8("prazo informado", dict(fonte="VAR_132", comentario="caixa da CK-C-12.4 (itens, prazo e motivo)"))],
    "SET-11": [M8("VAR-137: itens", dict(fonte=None, acao="EQUIPE",
                                         comentario="o checklist pergunta as atividades para o equipamento, sem separar "
                                                    "por item")),
               M8("montagem, instalação", dict(fonte="CK_P_11_3", formato="LISTA_TEXTO", inicial_minuscula=True)),
               M8("certificados, laudos", dict(fonte="CK_P_11_4")),
               M8("critérios objetivos", dict(fonte="CK_P_11_5"))],
    "SET-12": [M8("público e quantidade", dict(fonte="CK_P_12_2")),
               M8("conteúdo mínimo [VAR-138]", dict(fonte="CK_P_12_3")),
               M8("carga horária mínima [VAR-138]", dict(fonte="CK_P_12_4")),
               M8("formato: prática", dict(fonte="CK_P_12_5", formato="LISTA_TEXTO", inicial_minuscula=True)),
               M8("antes da utilização", dict(fonte="CK_P_12_6", inicial_minuscula=True))],
    "SET-13": [M8("VAR-139: serviços", dict(fonte="CK_P_13_4", formato="LISTA_TEXTO", inicial_minuscula=True)),
               M8("no local de instalação", dict(fonte="CK_P_13_5", acao="ESCOLHA", grupo="local_atendimento",
                                                 opcoes=[o(eq("CK_P_13_5", "Sim"), "no local de instalação")],
                                                 comentario="texto do próprio marcador com a CK-P-13.5 = Sim; com 'Não' "
                                                            "ou 'Depende do defeito', a equipe redige")),
               M8("[VAR-140]", dict(fonte="CK_P_13_6", inicial_minuscula=True,
                                    comentario="prazo máximo para início do atendimento (opção da CK-P-13.6)")),
               M8("[VAR-141]", dict(fonte="CK_P_13_3", inicial_minuscula=True)),
               M8("Equipamento substituto", dict(fonte="VAR_152", acao="OPCIONAL", quando=tem("VAR_152"),
                                                 texto="Equipamento substituto: {valor}.", remove_antes=" ",
                                                 comentario="trecho do próprio marcador, sem a remissão ao TR-5.14; "
                                                            "entra com a caixa da CK-P-13.8"))],
    "SET-14": [M8("VAR-148: periodicidade]", dict(fonte="CK_P_14_5_texto")),
               M8("periodicidade e comprovação", dict(fonte="CK_P_14_6_texto")),
               M8("VAR-149", dict(fonte="VAR_149")),
               M8("[VAR-140]", dict(fonte="CK_P_14_3_texto", alternativas=["CK_P_13_6"],
                                    comentario="prazo do atendimento presencial (caixa da CK-P-14.3); sem ela, o prazo "
                                               "de início do atendimento (CK-P-13.6)"))],
    "SET-15": [M8("VAR-009", dict(fonte="VAR_009", formato="LISTA_TEXTO", inicial_maiuscula=True))],
    "SET-16": [M8("módulos e tipo de licença", dict(fonte="CK_P_15_3_texto")),
               M8("atualizações de software", dict(fonte="CK_P_15_6", acao="ESCOLHA", grupo="atualizacoes",
                                                   opcoes=[o(eq("CK_P_15_6", "Sim"), "atualizações de software ou "
                                                             "firmware durante a garantia, sem custo adicional")],
                                                   comentario="texto do próprio marcador com a CK-P-15.6 = Sim"))],
    "SET-17": [M8("[VAR-143]. ", dict(fonte="VAR_143")),
               M8("Se CK-P-9.5 = Sim", dict(fonte="CK_P_9_5_texto", acao="OPCIONAL", quando=eq("CK_P_9_5", "Sim"),
                                            texto="o Contratado apresentará levantamento técnico do local (site "
                                                  "planning) com o conteúdo {valor}, no prazo definido pela equipe.",
                                            inicial_maiuscula=True, remove_antes=" ",
                                            comentario="trecho do próprio marcador; o [VAR-143] de dentro vira a caixa da "
                                                       "CK-P-9.5"))],
    "SET-18": [M8("equipamento e local", dict(fonte=None, acao="EQUIPE",
                                              comentario="o checklist não pede o equipamento a retirar nem o local")),
               M8("descontaminação", dict(fonte="VAR_144", comentario="CK-P-20.3 e caixa da CK-P-20.2"))],
    "SET-19": [M8("VAR-150", dict(fonte="VAR_150", acao="ESCOLHA", grupo="manuais",
                                  opcoes=[o(e(eq("CK_P_16_6", "Sim"), tem("VAR_150")),
                                            "manuais de operação, manutenção e segurança e demais documentos técnicos "
                                            "({valor})"),
                                          o(eq("CK_P_16_6", "Sim"),
                                            "manuais de operação, manutenção e segurança e demais documentos técnicos")],
                                  comentario="texto do próprio marcador com a CK-P-16.6 = Sim; outros documentos da "
                                             "caixa (VAR-150) entre parênteses"))],
    "SET-20": [M8("[VAR-146]. ", dict(fonte="CK_C_16_1", alternativas=["CK_P_19_1"], formato="LISTA_TEXTO",
                                      inicial_minuscula=True)),
               M8("instalação, testes e treinamento", dict(fonte="CK_P_19_2_texto",
                                                           comentario="etapas da caixa da CK-P-19.2; no consumo, equipe")),
               M8("[VAR-145]", dict(fonte="VAR_145", formato="LISTA_TEXTO")),
               M8("situações de recusa", dict(fonte="CK_C_16_2", alternativas=["CK_P_19_4"]))],
    "SET-21": [M8("VAR-074", dict(fonte="VAR_074", formato="NUMERO_EXTENSO", texto="{valor} dias")),
               M8("VAR-151", dict(fonte="VAR_151", formato="LISTA_TEXTO", inicial_minuscula=True))],
    "SET-22": [M8("materiais e situações", dict(fonte="VAR_147"))],
    "SET-23": [M8("VAR-161", dict(fonte="VAR_161", formato="NUMERO_EXTENSO"))],
}


def marcadores_m08(texto):
    """trechos entre colchetes de primeiro nível, na ordem."""
    out, nivel, ini = [], 0, 0
    for i, ch in enumerate(texto):
        if ch == "[":
            if nivel == 0:
                ini = i
            nivel += 1
        elif ch == "]" and nivel:
            nivel -= 1
            if nivel == 0:
                out.append(texto[ini:i + 1])
    return out


def montar_m08(m08, erros):
    for r in m08:
        marc = marcadores_m08(r["texto_proposto"])
        ent = M08_MAPA.get(r["id"], [])
        if len(ent) != len(marc):
            erros.append(f"{r['id']}: {len(marc)} marcadores x {len(ent)} entradas no mapa")
            r["lacunas_mapa"] = ""
            continue
        if not marc:
            r["lacunas_mapa"] = ""
            continue
        t, cursor, saida = r["texto_proposto"], 0, []
        for mk, (confere, d) in zip(marc, ent):
            p0 = t.find(mk, cursor)
            if confere not in t[max(0, p0 - 40):p0 + len(mk) + 2]:
                erros.append(f"{r['id']}: marcador '{mk[:40]}' não contém '{confere}'")
            p = t.find(mk, cursor)
            ps = posicoes(t, mk)
            y = {"marcador": mk, "ocorrencia": ps.index(p) + 1, "fonte": d.get("fonte")}
            y.update({k: v for k, v in d.items() if k != "fonte"})
            if y["fonte"] is None and y.get("acao", "PREENCHER") == "PREENCHER":
                erros.append(f"{r['id']}: fonte null sem ação")
            saida.append(y)
            cursor = p + len(mk)
        r["lacunas_mapa"] = json.dumps(saida, ensure_ascii=False, separators=(",", ":"))
        if "Fase 14 (23/10/2026): lacunas_mapa" not in r["fonte"]:
            r["fonte"] = (r["fonte"].rstrip() + " Fase 14 (23/10/2026): lacunas_mapa INFERIDO (P36, decisão do gestor), "
                          "sem mudar o texto_proposto.")


# -------------------------------------------------------------------- conferência
def posicoes(texto, marcador):
    out, i = [], 0
    while True:
        p = texto.find(marcador, i)
        if p < 0:
            return out
        out.append(p)
        i = p + len(marcador)


def montar(m02):
    log, erros = [], []
    por_id = {r["id"]: r for r in m02}
    for b in M:
        if b not in por_id:
            erros.append(f"{b}: bloco inexistente no M02")
    for b in TABELAS:
        if b not in por_id:
            erros.append(f"{b}: tabela inexistente no M02")
    for r in m02:
        marc = [x for x in r["lacunas"].split(" | ") if x] if r["lacunas"].strip() else []
        if not marc:
            if r["id"] in M:
                erros.append(f"{r['id']}: mapa sem marcadores na coluna lacunas")
            r["lacunas_mapa"] = ""
            continue
        ent = M.get(r["id"])
        if ent is None:
            erros.append(f"{r['id']}: bloco com marcador sem mapa")
            continue
        if sorted(x["marcador"] for x in ent) != sorted(marc):
            erros.append(f"{r['id']}: marcadores {[x['marcador'] for x in ent]} x coluna lacunas {marc}")
            continue
        if [x["marcador"] for x in ent] != marc:
            log.append(f"{r['id']}: a coluna lacunas não está na ordem do texto; o mapa segue o texto")
        texto, cursor, saida = r["texto_literal"], 0, []
        for x in ent:
            p = texto.find(x["marcador"], cursor)
            ps = posicoes(texto, x["marcador"])
            if p < 0 or p not in ps:
                erros.append(f"{r['id']}: '{x['marcador']}' fora de ordem ou sobreposto")
                break
            y = {"marcador": x["marcador"], "ocorrencia": ps.index(p) + 1, "fonte": x["fonte"]}
            y.update({k: v for k, v in x.items() if k not in ("marcador", "fonte")})
            for k in ("estende_desde", "estende_ate", "remove_antes"):
                if k in y:
                    ok = (texto[:p].endswith(y[k]) if k in ("estende_desde", "remove_antes")
                          else texto[p + len(x["marcador"]):].startswith(y[k]))
                    if not ok and k != "remove_antes":
                        erros.append(f"{r['id']}: {k} '{y[k]}' não está junto do marcador")
            if y.get("fonte") is None and y.get("acao") in (None, "PREENCHER"):
                erros.append(f"{r['id']}: fonte null sem ação")
            if y.get("acao") == "EQUIPE" and not y.get("comentario"):
                erros.append(f"{r['id']}: fonte null sem motivo")
            saida.append(y)
            cursor = p + len(x["marcador"])
        r["lacunas_mapa"] = json.dumps(saida, ensure_ascii=False, separators=(",", ":"))
    for r in m02:
        r["tabela_colunas"] = json.dumps(TABELAS[r["id"]], ensure_ascii=False, separators=(",", ":")) \
            if r["id"] in TABELAS else ""
        if (r["lacunas_mapa"] or r["tabela_colunas"]) and "Fase 13 (23/10/2026)" not in r["fonte"]:
            r["fonte"] = r["fonte"].rstrip() + " " + FONTE
    n = sum(1 for r in m02 if r["lacunas_mapa"])
    acoes = {}
    for r in m02:
        for x in json.loads(r["lacunas_mapa"] or "[]"):
            acoes[x.get("acao", "PREENCHER")] = acoes.get(x.get("acao", "PREENCHER"), 0) + 1
    log.append(f"M02.lacunas_mapa: {n} blocos com marcador; marcadores por ação {dict(sorted(acoes.items()))}; "
               f"tabela_colunas: {sorted(TABELAS)}")
    # marcadores que parecem lacuna no texto e não estão na coluna lacunas (informativo)
    padrao = re.compile(r"\[[^\]]{1,200}\]|\.{4,}|_{3,}|\bX{2,}\b|xxxxx")
    for r in m02:
        if r["formatacao"] in ("PRETO",) or r["item_modelo"] == "OU":
            continue
        resto = r["texto_literal"]
        for mk in [x for x in r["lacunas"].split(" | ") if x]:
            resto = resto.replace(mk, "", 1)
        achados = [a for a in padrao.findall(resto) if a.strip(".") or len(a) >= 4]
        if achados and r["id"] not in TABELAS:
            log.append(f"aviso {r['id']}: trecho com cara de lacuna fora da coluna lacunas: {achados[:4]}")
    return erros, log


def main():
    pasta = Path(sys.argv[1])
    m02 = ler_csv(pasta / "M02_tr_blocos.csv")
    cols = [c for c in m02[0] if c not in ("lacunas_mapa", "tabela_colunas")]
    k = cols.index("lacunas") + 1
    cols = cols[:k] + ["lacunas_mapa", "tabela_colunas"] + cols[k:]
    erros, log = montar(m02)
    m08 = ler_csv(pasta / "M08_clausulas_setoriais.csv")
    cols8 = [c for c in m08[0] if c != "lacunas_mapa"]
    k8 = cols8.index("texto_proposto") + 1
    cols8 = cols8[:k8] + ["lacunas_mapa"] + cols8[k8:]
    montar_m08(m08, erros)
    if erros:
        raise SystemExit("f13_lacunas:\n" + "\n".join(erros))
    gravar_csv(pasta / "M02_tr_blocos.csv", cols, m02, preservar=())
    gravar_csv(pasta / "M08_clausulas_setoriais.csv", cols8, m08, preservar=())
    n8 = sum(len(json.loads(r["lacunas_mapa"])) for r in m08 if r["lacunas_mapa"])
    log.append(f"M08.lacunas_mapa: {sum(1 for r in m08 if r['lacunas_mapa'])} cláusulas com marcador, {n8} marcadores")
    # P37: toda opção que dá valor padrão (sem ter sido informado) fica marcada com padrao: true
    for nome, linhas_ in (("M02", m02), ("M08", m08)):
        for r in linhas_:
            for x in json.loads(r.get("lacunas_mapa") or "[]"):
                for op in x.get("opcoes", []):
                    if op.get("padrao"):
                        log.append(f"padrao: {nome} {r['id']} '{x['marcador'][:50]}' -> '{op['texto']}' "
                                   f"({x.get('comentario', '')[:120]})")
    Path(sys.argv[2]).write_text("\n".join(log) + "\n", encoding="utf-8")
    print(log[-1])


if __name__ == "__main__":
    main()
