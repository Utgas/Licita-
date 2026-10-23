#!/usr/bin/env python3
"""Gera sugestoes_checklist.md a partir do M11 (listas e contagens calculadas aqui; propostas escritas abaixo).

Uso: python3 -I ck_sugestoes.py <pasta_Matrizes_v1>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import ler_csv  # noqa: E402

# id, tipo, perguntas, problema, proposta, efeito no sistema
S = [
    ("S01", "DUPLICIDADE", "CK-C-13.5; CK-C-20.1",
     "As duas perguntas tratam do espaço de armazenamento ('A unidade dispõe de estrutura adequada para armazenar os itens?' e "
     "'A unidade possui espaço adequado para armazenamento?').",
     "Manter a 13.5 com a redação 'A unidade dispõe de espaço e estrutura adequados para armazenar os itens, inclusive nas "
     "condições de conservação exigidas? ☐ Sim ☐ Não. Se não, informe a providência e o prazo.' e excluir a 20.1.",
     "Hoje a divergência entre as duas dispara VAL-022; com a exclusão, a 13.5 alimenta sozinha a WZ-47."),
    ("S02", "DUPLICIDADE", "CK-C-5.5; CK-C-5.6; CK-C-6.1; CK-P-5.5; CK-P-5.6; CK-P-6.1",
     "A 6.1 ('Existe mais de um fabricante ou fornecedor capaz de atender à necessidade?') repete a 5.5 e a 5.6, nos dois "
     "checklists.",
     "Excluir a 6.1 e abrir a seção 6 com: '6.1 Considerando as respostas 5.5 e 5.6, a área técnica pretende indicar produto, "
     "fabricante ou fornecedor exclusivo?' (a atual 6.2), renumerando as seguintes.",
     "Hoje a divergência dispara VAL-023; com a exclusão, a regra deixa de ser necessária."),
    ("S03", "DUPLICIDADE", "CK-C-CAB.02; CK-C-1.1; CK-C-CAB.04; CK-C-1.4; CK-P-CAB.02; CK-P-1.1; CK-P-CAB.04; CK-P-1.4",
     "OMS requisitante e responsável técnico aparecem no cabeçalho e de novo na seção 1.",
     "Manter só a seção 1 (com posto, telefone e e-mail) e deixar no cabeçalho apenas número do processo e data.",
     "O M11 dá prioridade à seção 1; a exclusão evita respostas diferentes para o mesmo dado."),
    ("S04", "AMBIGUIDADE", "CK-C-12.2",
     "'O prazo solicitado é menor ou maior que 30 dias?' com Sim e Não: 'Sim' não diz se é menor ou maior, e 'Não' pode "
     "significar 'igual a 30 dias' ou 'não sei'.",
     "'12.2 O prazo escolhido na 12.1 é diferente de 30 dias? ☐ Não ☐ Sim. Se sim, explique por que o prazo de 30 dias não "
     "atende.'",
     "O M11 já lê a 12.2 assim (condicional implícita e VAL-020)."),
    ("S05", "AMBIGUIDADE", "{LISTA_ESCOLHA}",
     "Nas perguntas com mais de duas opções, o checklist não diz se é para marcar uma ou várias. O M11 inferiu "
     "{N_MULTIPLA} como MULTIPLA e {N_UNICA} como UNICA.",
     "Acrescentar ao fim do enunciado '(marque uma opção)' ou '(marque todas as que se aplicam)'. O checklist de permanentes "
     "já faz isso na 2.3 e na 18.3.",
     "Sem a instrução, duas marcas numa pergunta UNICA viram pendência de leitura (VAL-037)."),
    ("S06", "AMBIGUIDADE", "CK-C-7.2",
     "A mesma lista mistura a resposta (Não, Sim) com as causas da variação.",
     "'7.2 A demanda poderá variar durante o período da contratação? ☐ Não ☐ Sim' e '7.2.1 Se sim, causa da variação: ☐ "
     "Variação do número de pacientes ☐ Alteração dos protocolos ☐ Consumo imprevisível ☐ Novos diagnósticos ☐ Surgimento de "
     "urgências ☐ Outro'.",
     "Separa o fato que sugere registro de preços (WZ-10, VAL-024) da explicação."),
    ("S07", "AMBIGUIDADE", "CK-C-14.1; CK-C-14.2; CK-P-13.1",
     "Validade e garantia são decididas item a item (ajuste 1), mas as perguntas pedem uma resposta só; a P-13.1 tem uma "
     "lacuna dentro da opção ('Outro: ______ meses').",
     "Trocar por tabela de uma linha por item: 'Item | Prazo total de validade | Validade mínima na entrega (12 meses / 75% do "
     "prazo total / dois terços do prazo total / outro critério: descrever)' no consumo, e 'Item | Garantia mínima (12 / 24 / "
     "36 / outro: meses)' nos permanentes.",
     "Preenche direto os atributos validade_minima (VAR-117) e garantia_minima_meses (VAR-124)."),
    ("S08", "AMBIGUIDADE", "CK-C-9.7; CK-C-16.5; CK-P-11.6; CK-P-17.5; CK-P-19.6",
     "Perguntas 'Quem...' levam a responder com nome de pessoa, que não deve ir para a minuta.",
     "Redigir 'Qual setor ou função realizará...?' e orientar a resposta por cargo ou função.",
     "O M11 trata essas perguntas como SO_CONTROLE (designação é ato interno)."),
    ("S09", "AMBIGUIDADE", "CK-C-8.1 a 8.4; CK-C-11.1 a 11.4",
     "As seções 8 e 11 perguntam de forma parecida sobre fornecimento por empresas diferentes: a 8 trata de itens diferentes "
     "no mesmo grupo e a 11 da divisão do mesmo item (cota de ME/EPP), mas o texto não deixa isso claro.",
     "Abrir a seção 11 com: 'As perguntas abaixo tratam da divisão da quantidade de um mesmo item entre fornecedores (cota "
     "reservada), não do agrupamento de itens diferentes (seção 8).'",
     "Evita que a resposta da seção 11 vire justificativa de grupo, ou o contrário (VAL-015, VAL-016)."),
    ("S10", "LACUNA", "CK-C-12 (nova 12.8)",
     "O checklist de consumo não pergunta o local de entrega (endereço, setor de recebimento e horário); o de permanentes "
     "pergunta o local por item (4.2).",
     "'12.8 Onde os itens serão entregues? Informe OMS, setor de recebimento, endereço e horário; se houver mais de um local, "
     "informe os itens de cada local.'",
     "Alimenta VAR-064 e TR-5.4 (NE-026 nota 2)."),
    ("S11", "LACUNA", "CK-C-12.3 (nova 12.3.1)",
     "Com entrega parcelada ou conforme pedidos, o checklist não pede a composição das parcelas nem o critério dos pedidos.",
     "'12.3.1 Se a entrega for parcelada, informe as parcelas (itens, quantidades e prazos) ou o critério dos pedidos (ex.: "
     "pedidos mensais conforme consumo).'",
     "Alimenta VAR-062 e TR-5.2.TAB1."),
    ("S12", "LACUNA", "CK-C-16 (nova 16.6)",
     "O checklist de consumo pergunta se a avaliação definitiva exige teste (16.4), mas não o prazo de que a equipe precisa; o "
     "de permanentes pergunta (19.3).",
     "'16.6 Qual prazo a equipe técnica precisa para concluir a avaliação definitiva? ☐ 2 dias úteis ☐ 5 dias úteis ☐ 10 dias "
     "úteis ☐ Outro'.",
     "Alimenta VAR-075 e WZ-34 (TR-8.3)."),
    ("S13", "LACUNA", "CK-C-21 (nova 21.5)",
     "O checklist de consumo não pergunta pelos critérios do Guia Nacional de Contratações Sustentáveis; o de permanentes "
     "pergunta (21.4).",
     "Repetir no consumo a pergunta 21.4 do checklist de permanentes, com item, requisito e forma de comprovação.",
     "Alimenta VAR-044, WZ-17 e TR-4.1.1..TR-4.1.3 (NE-011)."),
    ("S14", "LACUNA", "CK-C-18.1",
     "A garantia técnica além da validade não identifica itens nem prazo.",
     "'18.1 Algum item precisa de garantia técnica além da validade? ☐ Não ☐ Sim. Se sim, informe os itens, o prazo e o "
     "motivo.'",
     "Alimenta WZ-29 e VAR-124 por item."),
    ("S15", "LACUNA", "CK-C-3.1; CK-P-3.1",
     "A tabela anexa pede CATMAT 'quando disponível'; sem código, o TR fica com a coluna CATMAT vazia.",
     "'A tabela deve conter, no mínimo: item, código CATMAT (ou classe e PDM, se ainda não houver código), descrição, "
     "unidade, quantidade...'",
     "Reduz o alerta VAL-039."),
    ("S16", "LACUNA", "cabeçalho dos dois checklists",
     "Objeto com bens de consumo e permanentes precisa dos dois checklists, mas nenhum deles diz isso.",
     "Orientação no cabeçalho: 'Se o processo tiver itens de consumo e permanentes, preencha os dois checklists e indique em "
     "cada um os itens que ele cobre.'",
     "Define a categoria de cada item (VAR-155) e a WZ-07 = AMBOS (VAL-040)."),
    ("S17", "LACUNA", "CK-C-7.6",
     "Quando outras OMS podem usar a contratação, o checklist não pede as OMS nem as quantidades estimadas por item.",
     "'7.6.1 Se sim, informe as OMS e, se souber, as quantidades estimadas por item.' (a confirmação vem da IRP).",
     "Apoia WZ-11, WZ-12 e VAR-029."),
    ("S18", "LACUNA", "CK-P-8.7",
     "O checklist de permanentes não pergunta por condição de temperatura ou umidade no transporte e na guarda até a "
     "instalação.",
     "Acrescentar às opções da 8.7: '☐ Controle de temperatura ou umidade (informe a faixa)'.",
     "Alimenta VAR-122 e SET-02 também para permanentes."),
    ("S19", "LEITURA", "os dois checklists",
     "As marcas de opção são o caractere '☐' digitado no texto, a numeração das perguntas é digitada e os dois arquivos usam "
     "estilos diferentes (o de consumo usa 'heading 1' e 'Normal'; o de permanentes, estilos próprios). Isso deixa a leitura "
     "automática dependente de texto (ver perguntas_abertas.md, P26).",
     "Trocar '☐' por controle de conteúdo de caixa de seleção do Word, pôr cada resposta em controle de texto com marca "
     "(tag) igual ao ID do M11 (ex.: CK-C-14.2) e usar o mesmo conjunto de estilos nos dois arquivos.",
     "Com marcas por pergunta, a leitura deixa de depender da posição do texto e a VAL-037 quase não dispara."),
    ("S20", "AMBIGUIDADE", "CK-C-12.1; CK-P-8.1",
     "Proposta do gestor (23/10/2026): o 'Outro' do prazo de entrega é texto livre, mas o prazo (VAR-060) é número de dias.",
     "Na próxima versão, trocar 'Outro' por 'Outro: ____ dias'.",
     "O 'Outro' precisa virar número de dias para preencher a VAR-060."),
    ("S21", "ESCOPO", "CK-C-10.1 a CK-C-10.11",
     "Proposta do gestor (23/10/2026): o comodato ficou fora do sistema (P24, decisão 0008), mas a seção 10 do consumo "
     "continua no Word.",
     "Manter a seção no Word; o sistema lê e guarda só para controle até o estudo do comodato.",
     "Nada da seção 10 vai para a minuta; WZ-56 e SET-01 desligadas."),
]

# o que cada sugestão virou no sistema (decisão 0009: o Word distribuído não muda)
NO_SISTEMA = {
    "S01": "M11, colunas leitura e revisao_expr da CK-C-13.5 e da CK-C-20.1: prevalece a 13.5; resposta diferente na 20.1 "
           "destaca as duas. A VAL-022 continua.",
    "S02": "M11, CK-C-6.1 e CK-P-6.1: prevalecem a 5.5 e a 5.6; contradição destaca a 6.1. A VAL-023 continua.",
    "S03": "M11, cabeçalho x seção 1: prevalece a seção 1 (a CK-x-CAB.02 e a CK-x-CAB.04 só preenchem quando a 1.1 e a 1.4 "
           "estão vazias); respostas diferentes ficam destacadas; a comparação do nome do responsável é feita na leitura "
           "(checklist.divergencias_leitura, P32).",
    "S04": "M11, CK-C-12.2: leitura 'o prazo da 12.1 é diferente de 30 dias?'; resposta que contradiz a VAR-060 fica "
           "destacada; a VAL-020 pede a explicação.",
    "S05": "M11, todas as perguntas que não são só de controle: duas marcas em pergunta de uma opção (checklist.marcas_multiplas) "
           "ou pergunta sem resposta ficam destacadas; nas de uma opção que preenchem a minuta, o sistema pergunta ao "
           "operador qual opção vale (revisao_pergunta) e a VAL-037 bloqueia até a resposta.",
    "S06": "M11, CK-C-7.2: 'Não' sozinho = demanda estável; 'Sim' ou causa = demanda variável; 'Não' com outra marca fica "
           "destacado.",
    "S07": "M11, CK-C-14.1, CK-C-14.2 e CK-P-13.1: resposta única vale para todos os itens do checklist, fica destacada "
           "(checklist.resposta_unica_por_item) e o sistema pede confirmação item a item.",
    "S08": "M11, perguntas 'Quem...' (CK-C-9.7, CK-C-16.5, CK-P-11.6, CK-P-17.5, CK-P-19.6): só controle, nunca vão à "
           "minuta, e ficam destacadas quando respondidas.",
    "S09": "M11, CK-C-8.1, CK-C-8.2, CK-C-11.2 e CK-C-11.4: resposta que parece trocada entre as seções 8 e 11 fica "
           "destacada; na 8.2, o sistema pergunta quais itens formam cada grupo.",
    "S10": "Complemento do operador CK-X-01 (local de entrega, VAR-064).",
    "S11": "Complemento do operador CK-X-02 (parcelas ou critério dos pedidos, VAR-062).",
    "S12": "Complemento do operador CK-X-03 (prazo da avaliação definitiva em dias úteis digitado, VAR-075).",
    "S13": "Complemento do operador CK-X-04 (critérios de sustentabilidade no consumo, VAR-044 e WZ-17).",
    "S14": "Complemento do operador CK-X-05 (garantia por item no consumo, VAR-124).",
    "S15": "Complemento do operador CK-X-06 (código CATMAT por item, VAR-157); item sem código continua na VAL-039.",
    "S16": "Complemento do operador CK-X-07 (categoria de cada item quando vêm os dois checklists, VAR-155).",
    "S17": "Complemento do operador CK-X-08 (OMS e quantidades estimadas, sugestão para a VAR-029; a IRP confirma).",
    "S18": "Complemento do operador CK-X-09 (faixa de temperatura ou umidade por item no permanente, VAR-122 e SET-02).",
    "S19": "Não se aplica ao Word distribuído. Fica como sugestão para uma versão futura do checklist, que terá M11 e "
           "pacote próprios.",
    "S20": "M11, CK-C-12.1 e CK-P-8.1: 'Outro' com número seguido de 'dias' vira o número (CK_x_numero, lido pelo motor, P32) e "
           "vai para a VAR-060; qualquer outra coisa fica destacada e o sistema pergunta o prazo em dias corridos.",
    "S21": "M11: CK-C-10.1 a CK-C-10.11 passaram a SO_CONTROLE, sem destino nem expressão; WZ-56 (depende_de_expr = false), "
           "SET-01 e VAL-027 (condicao_expr = false) desligadas com o motivo no texto.",
}


def main():
    pasta = Path(sys.argv[1])
    m11 = ler_csv(pasta / "M11_checklist.csv")
    exclusivas = {"Sim", "Não", "Não sei informar", "Não se aplica", "Parcialmente", "Ainda não foi avaliada",
                  "Ainda não definido", "Depende do defeito", "Tecnicamente inviável/não se aplica", "Não foi localizado",
                  "Não se aplica ao objeto", "Não existe estoque", "Não existem equipamentos semelhantes"}

    def opcoes(r):
        return [o.strip() for o in r["opcoes"].split("campos:")[0].split("; ") if o.strip()]
    escolha = [r for r in m11 if r["tipo_resposta"] in ("UNICA", "MULTIPLA") and r["efeito"] != "SO_CONTROLE" and
               len(opcoes(r)) > 2 and not set(opcoes(r)) <= exclusivas and
               not any(x in r["orientacao"] for x in ("Marque todas", "Marque apenas"))]
    n_multi = sum(1 for r in escolha if r["tipo_resposta"] == "MULTIPLA")
    n_unica = sum(1 for r in escolha if r["tipo_resposta"] == "UNICA")
    lista = "; ".join(r["id"] for r in escolha)
    out = ["# Sugestões para a revisão dos checklists técnicos", "",
           "Base: M11_checklist.csv (leitura dos dois docx, hashes no README). O checklist de consumo está em revisão; as "
           "propostas abaixo vêm das lacunas, duplicidades e ambiguidades encontradas ao mapear cada pergunta para o sistema. "
           "Cada item traz a pergunta afetada, o problema, a redação proposta e o efeito no sistema.", "",
           "Situação em 23/10/2026 (decisão 0009): o dono do projeto aceitou S01 a S19 e o gestor acrescentou S20 e S21. Os dois "
           "checklists em Word já foram distribuídos e não mudam; por isso cada sugestão virou regra de leitura, destaque, "
           "pergunta ao operador ou complemento no M11 (linha 'No sistema'). As propostas de redação ficam para uma versão "
           "futura do checklist.", "",
           f"Resumo: {len(S)} sugestões ({sum(1 for s in S if s[1] == 'DUPLICIDADE')} duplicidades, "
           f"{sum(1 for s in S if s[1] == 'AMBIGUIDADE')} ambiguidades, {sum(1 for s in S if s[1] == 'LACUNA')} lacunas e "
           f"{sum(1 for s in S if s[1] == 'LEITURA')} sobre leitura automática e "
           f"{sum(1 for s in S if s[1] == 'ESCOPO')} de escopo).", ""]
    for sid, tipo, perg, prob, prop, efeito in S:
        perg = perg.replace("{LISTA_ESCOLHA}", f"{len(escolha)} perguntas: {lista}")
        prob = prob.replace("{N_MULTIPLA}", str(n_multi)).replace("{N_UNICA}", str(n_unica))
        out += [f"## {sid}. {tipo.capitalize()}", "", f"- **Perguntas:** {perg}", f"- **Problema:** {prob}",
                f"- **Proposta:** {prop}", f"- **Efeito no sistema:** {efeito}",
                f"- **No sistema (decisão 0009):** {NO_SISTEMA[sid]}", ""]
    # mapeamento dos atributos de item nos dois checklists (tarefa 5)
    out += ["## Atributos de item: pergunta de origem em cada checklist", "",
            "| Atributo (M05) | Consumo | Permanentes |", "|---|---|---|",
            "| grupo (VAR-112) | CK-C-8.2 | CK-P-7.2 (e CK-P-7.5, acessório dependente) |",
            "| exige_amostra (VAR-114) | CK-C-9.1 e CK-C-9.2 | CK-P-17.1 e CK-P-17.2 (demonstração, teste, prova de conceito ou amostra) |",
            "| marca_indicada (VAR-115) | CK-C-3.4, CK-C-5.7 e seção 6 (CK-C-6.2 a 6.7) | CK-P-3.7 e seção 6 (CK-P-6.2 a 6.7) |",
            "| compatibilidade (VAR-121) | CK-C-3.3 | CK-P-3.3 |",
            "| perecivel e validade_minima (VAR-116, VAR-117) | CK-C-14.1 e CK-C-14.2 | sem pergunta (não se aplica a permanentes) |",
            "| faixa_temperatura (VAR-122) | CK-C-13.1 | complemento do operador CK-X-09 (S18) |",
            "| controle_especial (VAR-123) | CK-C-15.2 | sem pergunta (não se aplica a equipamentos) |",
            "| garantia_minima_meses (VAR-124) | complemento do operador CK-X-05 (S14) | CK-P-13.1 |",
            "| categoria (VAR-155) | checklist em que o item aparece (CK-C-1.5); com os dois checklists, complemento CK-X-07 (S16) | checklist em que o item aparece (CK-P-1.5); com os dois, CK-X-07 |", ""]
    (pasta / "sugestoes_checklist.md").write_text("\n".join(out), encoding="utf-8")
    print(f"sugestoes_checklist.md: {len(S)} sugestões; perguntas de escolha sem instrução: {len(escolha)} "
          f"(MULTIPLA {n_multi}, UNICA {n_unica})")


if __name__ == "__main__":
    main()
