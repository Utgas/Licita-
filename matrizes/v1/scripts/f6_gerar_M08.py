#!/usr/bin/env python3
"""Fase 6 - M08: cláusulas setoriais (saúde) que o modelo AGU DEZ/2025 não traz.

Uso: python3 -I f6_gerar_M08.py <pasta_Matrizes_v1>

Especificação reconstruída (ver README). Fonte principal: as seções dos checklists técnicos (comodato, transporte,
validade, requisitos sanitários, autorizações da empresa e, no de permanentes, instalação, treinamento, garantia,
assistência, software, infraestrutura e desinstalação). O corpus entra só como evidência de redação (trecho e página),
nunca como prova de que a cláusula está correta. Os TRs 117/2025, 140/2025 e 190/2025 aparecem aqui só como prática.
A redação proposta é minha (INFERIDO): usa [VAR-xxx] para o que vem do checklist e não inventa prazo, quantidade,
percentual ou preço. Cada cláusula se apoia em nota do modelo que admite acréscimo (NE-010 nota 2 na seção 4;
NE-024 nota 1 na seção 5; NE-026 nota 2 no local de entrega) ou preenche bloco já existente do M02.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comum import gravar_csv, ler_csv  # noqa: E402
from jlogic import algum_item, ck, dumps, e, eq, inn, ne, ou, tem, var  # noqa: E402

COLS = ["id", "tema", "documento", "origem_checklist", "condicao", "condicao_expr", "ponto_insercao", "texto_proposto",
        "variaveis", "perguntas_wz", "base_no_modelo", "evidencia_corpus", "observacao", "fonte", "status"]

C, P = "C", "P"
SIM = "Sim"
TR117 = "TR 117/2025 (TR exemplos/Termo de Referência-3.pdf)"
TR190 = "TR 190/2025 (TR exemplos/1e19dfeb-ac58-4ae4-aa3c-8114737d3f86.pdf)"
TR23 = "TR 23/2026 (TR exemplos/ae4297a4-a494-4822-980f-6cbcc6b4571c.pdf)"
TR58 = "TR 58/2026 (TR exemplos/f518d222-2d93-4dd0-8068-55769fe133c5.pdf)"
ETP117 = "ETP 117/2025 (ETP exemplos/Estudo Técnico Preliminar-2.pdf)"
ETP99 = "ETP 99/2025 (ETP exemplos/d4ef8f94-2e0a-4181-8d58-22ed3bdf305c.pdf)"
ETP19 = "ETP 19/2026 (ETP exemplos/39f4f8bb-fab9-4793-bbba-6d8cc9196eab.pdf)"


def sim(lista, n):
    return eq(ck(lista, n), SIM)


def nao_lista(lista, n, opcao):
    """a resposta MULTIPLA não é só a opção dada (ex.: marcou algo além de 'Não')"""
    return {"!": [{"==": [var(ck(lista, n)), [opcao]]}]}


def marcado(lista, n, opcao):
    return inn(opcao, var(ck(lista, n)))


S = [
    dict(id="SET-01", tema="Comodato de equipamento vinculado ao fornecimento de material de consumo",
         documento="AMBOS", origem="CK-C-10.1 a CK-C-10.11",
         condicao="DESLIGADA: comodato fora do sistema por enquanto (P24, decisão 0008 de 23/10/2026); condicao_expr = false, "
                  "a cláusula nunca entra. Condição anterior: SE o checklist de consumo indicar dependência de equipamento "
                  "em comodato (CK-C-10.1 = Sim) E a equipe administrativa admitir o comodato (WZ-56 = SIM)",
         expr=False,
         ponto="TR: seção 5, depois de TR-5.4.1, como subitem próprio 'Comodato'; ETP: ETP-06.01 (descrição da solução) e "
               "ETP-04.01 (requisitos)",
         texto="Para o fornecimento dos itens [VAR-125: itens que dependem do equipamento], o Contratado disponibilizará ao "
               "Contratante, em comodato e sem ônus adicional, [VAR-125: quantidade e descrição do equipamento], durante a "
               "vigência da contratação, incluídos [VAR-126: instalação, treinamento e manutenção, conforme o checklist]. Em caso "
               "de falha que impeça o uso, o Contratado reparará ou substituirá o equipamento no prazo máximo de [VAR-127], "
               "sem prejuízo do fornecimento dos materiais.",
         vars_="VAR-125; VAR-126; VAR-127", wz="WZ-56; WZ-08",
         base="Nenhuma nota trata de comodato. Acréscimo apoiado em NE-024 nota 1 (seção 5 adaptável) e NE-010 nota 2 "
              "(requisitos técnicos adicionais)",
         evid=f"{TR117} p.2: 'Em caso de pane que interrompa o funcionamento do equipamento em comodato com a impossibilidade de "
              f"uso do item licitado, caberá a Contratada o ônus do item, manutenção do equipamento'; {ETP117} p.11: 'A entrega "
              f"dos materiais que necessitam de aparelho em comodato será em 7 (sete) dias antes da cirurgia.'",
         obs="O enquadramento jurídico do comodato numa aquisição (obrigação acessória, instrumento próprio, custo embutido no "
             "preço do material) não está no modelo nem nas notas: decisão da equipe administrativa (WZ-56, status A_VERIFICAR).",
         status="A_VERIFICAR"),
    dict(id="SET-02", tema="Transporte e conservação (temperatura, cadeia de frio, luz, umidade, produto controlado, "
                           "logística especial)",
         documento="AMBOS", origem="CK-C-13.1; CK-C-13.2; CK-C-13.3; CK-P-8.6; CK-P-8.7",
         condicao="SE algum item tiver faixa de temperatura OU o checklist marcar cuidado especial de transporte "
                  "(CK-C-13.3) OU logística especial para permanentes (CK-P-8.7 = Sim)",
         expr=ou(algum_item(tem("faixa_temperatura")), sim(C, "13.1"), tem(ck(C, "13.3")), sim(P, "8.7")),
         ponto="TR: seção 5 (Condições de entrega), depois de TR-5.4; ETP: ETP-04.01",
         texto="Os itens [VAR-122 e VAR-128: itens e cuidados] serão transportados, armazenados até a entrega e entregues nas "
               "condições de conservação indicadas pelo fabricante, observada a faixa de temperatura [VAR-122] [e com registro "
               "contínuo da temperatura durante o transporte, apresentado no ato da entrega (VAR-129)]. [Para permanentes: o "
               "Contratado providenciará a logística especial de transporte e movimentação descrita em VAR-128.] O "
               "descumprimento das condições de conservação é motivo de recusa (TR-8.2).",
         vars_="VAR-122; VAR-128; VAR-129", wz="",
         base="NE-024 nota 1 (seção 5 adaptável); NE-010 nota 2",
         evid=f"{ETP99} p.2: 'Realizar transporte em veículos qualificados, com controle e registro de temperatura e umidade "
              f"sempre que aplicável.'; {TR58} p.5: '5.2.1. Será de responsabilidade da CONTRATADA, caso necessário, a obtenção "
              f"de autorizações ou licenças para o transporte e movimentação do equipamento em vias públicas'",
         obs="O ETP 99/2025 cita RDC 304/2019 e Decreto 10.388/2020 para o transporte; não conferidos em fonte oficial "
             "(M07, NAO_CONFERIDA): a redação proposta não cita norma.", status="INFERIDO"),
    dict(id="SET-03", tema="Documentos que acompanham a entrega (certificado de análise, laudo do lote, rastreabilidade, "
                           "registro de temperatura)",
         documento="TR", origem="CK-C-13.4; CK-C-15.4",
         condicao="SE o checklist pedir documento na entrega (CK-C-13.4 com opção marcada OU CK-C-15.4 = Sim)",
         expr=ou(tem(ck(C, "13.4")), sim(C, "15.4")),
         ponto="TR: seção 5, depois de TR-5.4 (e conferência em TR-8.1)",
         texto="A entrega dos itens [VAR-130: itens] será acompanhada de [VAR-130: documentos exigidos, ex.: certificado de "
               "análise do lote, laudo, documento de rastreabilidade, registro de temperatura], sem os quais o recebimento "
               "provisório não será feito.",
         vars_="VAR-130", wz="", base="NE-024 nota 1; NE-026 nota 1 (regras de recebimento no TR Digital)",
         evid=f"{TR117} p.6: 'presença de instrução de uso e etiquetas de rastreabilidade com identificação do fabricante, lote "
              f"ou série, validade e registro na Anvisa'",
         obs="", status="INFERIDO"),
    dict(id="SET-04", tema="Validade remanescente inferior à mínima, em caráter excepcional, com compromisso de substituição",
         documento="TR", origem="CK-C-14.4; CK-C-14.5",
         condicao="SE a equipe administrativa admitir a exceção (WZ-57 = SIM), com base em CK-C-14.4 = Sim",
         expr=e(eq("WZ_57", "SIM"), sim(C, "14.4")),
         ponto="TR: seção 5, logo depois de TR-5.4.1",
         texto="Em caráter excepcional, nas situações [VAR-133], poderá ser aceito item com validade remanescente inferior à "
               "exigida no subitem de validade mínima, desde que o Contratado apresente compromisso escrito de substituir, sem "
               "ônus para o Contratante, o produto que não for consumido antes do vencimento [VAR-134].",
         vars_="VAR-133; VAR-134", wz="WZ-57; WZ-09",
         base="TR-5.4.1 (validade mínima por item, VAR-117); NE-024 nota 1",
         evid=f"{TR190} p.4: 'Em casos de urgência no recebimento, que serão comunicados pelo Hospital, poderão ser aceitos itens "
              f"com a validade inferior a 75%, desde que a contratada se comprometa a trocá-lo no caso de término de validade'",
         obs="A validade mínima de cada item não é cláusula setorial: vem da CK-C-14.2 por item (VAR-117) e preenche TR-5.4.1.",
         status="INFERIDO"),
    dict(id="SET-05", tema="Registro ou notificação do produto na Anvisa",
         documento="AMBOS", origem="CK-C-15.1; CK-P-16.1",
         condicao="SE o checklist indicar que os produtos precisam de registro ou notificação na Anvisa",
         expr=ou(sim(C, "15.1"), sim(P, "16.1")),
         ponto="TR: seção 4 (Requisitos da contratação), depois de TR-4.1.3; ETP: ETP-04.01",
         texto="Só será admitida a oferta de produto com registro ou notificação vigente na Anvisa. O produto entregue deverá "
               "corresponder ao registro ou à notificação informados na proposta.",
         vars_="", wz="",
         base="NE-010 nota 2 (requisitos técnicos adicionais na seção 4)",
         evid=f"{TR58} p.2: '4.1.1 Só será admitida a oferta de produto previamente notificado/registrado na ANVISA, conforme a Lei "
              f"nº 6.360, de 1976 e Decreto nº 8.077, de 2013'; {TR117} p.6: 'O registro ANVISA cadastrado na proposta devera "
              f"compreender ao mesmo do material entregue'",
         obs="A Lei 6.360/1976 está na base (NE-073); o Decreto 8.077/2013 só no corpus (M07, NAO_CONFERIDA). A redação proposta "
             "não cita norma até a equipe decidir a remissão.", status="INFERIDO"),
    dict(id="SET-06", tema="Item sujeito a controle especial: Autorização Especial da empresa (requisito de lei especial)",
         documento="TR", origem="CK-C-15.2; CK-C-15.3; CK-C-17.5",
         condicao="SE algum item estiver sujeito a controle especial (atributo controle_especial = S, vindo da CK-C-15.2)",
         expr=algum_item(eq("controle_especial", "S")),
         ponto="TR: preenche TR-9.35 (Prova de atendimento aos requisitos previstos em lei especial), com WZ-38 incluindo "
               "REQUISITO_DE_LEI_ESPECIAL",
         texto="TR-9.35 preenchido com: Autorização Especial (AE) da Anvisa, vigente, para os itens [VAR-123: itens com controle "
               "especial], com o fundamento indicado pela equipe administrativa.",
         vars_="VAR-123; VAR-136", wz="WZ-38",
         base="NE-073: 'a exigência, dentre os documentos de habilitação técnica, da chamada Autorização Especial, emitida pela "
              "Agência Nacional de Vigilância Sanitária – Anvisa, nas contratações para aquisição de medicamentos sujeitos a "
              "controle especial'",
         evid=f"{TR58} p.15: '9.33. Autorização de Funcionamento (AE) vigente, emitida pela ANVISA, para os produtos abrangidos "
              f"pelo art. 3º da RDC nº 16, de 1º de abril de 2014, da ANVISA.'",
         obs="O corpus chama a AE de 'Autorização de Funcionamento (AE)'; a NE-073 a chama de Autorização Especial (M09, VAL-041).",
         status="INFERIDO"),
    dict(id="SET-07", tema="Requisitos sanitários e técnicos do produto (esterilidade, ausência de látex, biocompatibilidade, "
                           "norma técnica, conformidade Inmetro, ambiente especial)",
         documento="AMBOS", origem="CK-C-15.5; CK-C-15.6; CK-C-15.7; CK-P-3.5; CK-P-16.2; CK-P-16.3",
         condicao="SE o checklist indicar algum desses requisitos para algum item",
         expr=ou(sim(C, "15.5"), sim(C, "15.6"), sim(C, "15.7"), eq(ck(P, "16.2"), SIM), sim(P, "16.3"),
                 e(tem(ck(P, "3.5")), nao_lista(P, "3.5", "Não"))),
         ponto="TR: seção 4, depois de TR-4.1.3; ETP: ETP-04.01",
         texto="Os itens [VAR-135: itens] deverão atender aos seguintes requisitos, comprovados [na proposta ou na entrega]: "
               "[VAR-135: requisito por item, ex.: esterilidade, ausência de látex, biocompatibilidade, norma técnica indicada "
               "pela área técnica, conformidade Inmetro, compatibilidade com ambiente especial].",
         vars_="VAR-135", wz="", base="NE-010 nota 2; NE-009 nota 5 (requisitos de qualidade, compatibilidade e segurança)",
         evid=f"{TR23} p.2: '4.1.2. Só será admitida a oferta de equipamentos médicos integrados (Cardioversores, Ventiladores, "
              f"etc.) que estejam devidamente notificados/registrados na ANVISA, conforme a Lei nº 6.360/1976, e que cumpram os "
              f"requisitos de conformidade do INMETRO (Portaria nº 384/2020)'",
         obs="A norma técnica entra como informada pela área técnica (CK-C-15.7, CK-P-16.3); o sistema não sugere norma.",
         status="INFERIDO"),
    dict(id="SET-08", tema="Autorizações sanitárias da empresa fornecedora (licença sanitária, AFE)",
         documento="TR", origem="CK-C-17.5; CK-C-15.3",
         condicao="SE o checklist marcar autorização sanitária indispensável (CK-C-17.5) E a equipe confirmar que a atividade "
                  "exige autorização para funcionar (WZ-39 = SIM)",
         expr=e(tem(ck(C, "17.5")), eq("WZ_39", "SIM")),
         ponto="TR: preenche TR-9.14 (ato de autorização para o exercício da atividade)",
         texto="TR-9.14 preenchido com: atividade [VAR-136: distribuição ou comércio dos produtos], órgão expedidor [VAR-136: "
               "vigilância sanitária ou Anvisa, conforme a autorização] e fundamento indicado pela equipe administrativa.",
         vars_="VAR-136; VAR-087", wz="WZ-39",
         base="NE-060: especificar documento, órgão expedidor e fundamento legal em TR-9.14",
         evid=f"{TR23} p.9: '9.12.1. a Autorização de Funcionamento (AFE) vigente, emitida pela ANVISA, para os produtos "
              f"abrangidos pela RDC nº 16, de 1º de abril de 2014, da ANVISA;'",
         obs="AE para controlados vai no SET-06 (TR-9.35, NE-073); AFE e licença sanitária vão aqui (TR-9.14, NE-060).",
         status="INFERIDO"),
    dict(id="SET-09", tema="Agendamento da entrega e restrições de horário, veículo e acesso",
         documento="TR", origem="CK-C-12.6; CK-C-12.7; CK-P-8.5; CK-P-8.6",
         condicao="SE o checklist indicar agendamento prévio ou restrição de acesso",
         expr=ou(sim(C, "12.6"), sim(C, "12.7"), sim(P, "8.5"), sim(P, "8.6")),
         ponto="TR: complementa TR-5.4 (endereço de entrega)",
         texto="A entrega será previamente agendada com [VAR-131: setor de recebimento], com antecedência mínima de [VAR-131], "
               "observadas as seguintes restrições: [VAR-131: horário, veículo, acesso, trajeto interno].",
         vars_="VAR-131; VAR-064", wz="WZ-28",
         base="NE-026 nota 2: 'se houver a necessidade de previamente se acordar a data ou hora de entrega com o setor de "
              "almoxarifado respectivo, deve-se especificar essa obrigação'",
         evid=f"{TR23} p.2: 'Horário: Segunda a quinta-feira, das 09:00h às 15:00h; sexta-feira, das 08:00h às 11:00h.'",
         obs="Endereços do corpus não são copiados para as matrizes.", status="INFERIDO"),
    dict(id="SET-10", tema="Entrega emergencial de itens específicos",
         documento="TR", origem="CK-C-12.4",
         condicao="SE o checklist indicar itens com entrega emergencial (CK-C-12.4 = Sim)",
         expr=sim(C, "12.4"),
         ponto="TR: seção 5, depois de TR-5.1 ou TR-5.2",
         texto="Para os itens [VAR-132: itens], em situação de urgência comunicada pelo Contratante, a entrega ocorrerá no "
               "prazo máximo de [VAR-132: prazo informado pela área técnica], contado da comunicação.",
         vars_="VAR-132", wz="WZ-27", base="NE-024 nota 1",
         evid=f"{TR117} p.6: 'em situações de urgência, a entrega deverá ocorrer no prazo máximo de 4 horas'",
         obs="O prazo vem do checklist; o sistema não sugere prazo.", status="INFERIDO"),
    dict(id="SET-11", tema="Instalação, montagem, testes e comissionamento (permanentes; equipamento em comodato)",
         documento="AMBOS", origem="CK-P-11.1 a CK-P-11.6 (a CK-C-10.7, de comodato, ficou só para controle: S21)",
         condicao="SE o checklist indicar instalação ou montagem especializada (CK-P-11.1 = Sim)",
         expr=sim(P, "11.1"),
         ponto="TR: seção 5, depois das condições de entrega; complementa TR-8.9 (texto em preto, que já põe a instalação "
               "como condição do recebimento); ETP: ETP-06.01",
         texto="O Contratado executará, nos itens [VAR-137: itens], as atividades [VAR-137: montagem, instalação, configuração, "
               "calibração, comissionamento, testes], e entregará [VAR-145: certificados, laudos ou relatórios]. A instalação "
               "será considerada concluída quando atendidos os critérios [VAR-137: critérios objetivos].",
         vars_="VAR-137; VAR-145", wz="WZ-08",
         base="TR-8.9 (preto); NE-024 nota 1; NE-071 nota 1 (instalação de equipamento sofisticado como atividade associada)",
         evid=f"{TR23} p.3: '5.6. Os equipamentos médicos embarcados deverão estar instalados, testados e acompanhados de seus "
              f"manuais em português e certificados de garantia.'",
         obs="Com WZ-08 = SIM, a atividade associada pode justificar atestado (WZ-38, NE-071).", status="INFERIDO"),
    dict(id="SET-12", tema="Treinamento de operação",
         documento="AMBOS", origem="CK-P-12.1 a CK-P-12.8; CK-C-18.4; CK-C-20.5 (a CK-C-10.8, de comodato, ficou só para "
                                   "controle: S21)",
         condicao="SE o checklist indicar treinamento (CK-P-12.1 ou CK-C-18.4 = Sim)",
         expr=ou(sim(P, "12.1"), sim(C, "18.4")),
         ponto="TR: seção 5; ETP: ETP-06.01",
         texto="O Contratado ministrará treinamento [VAR-138: público e quantidade aproximada], com o conteúdo mínimo [VAR-138], "
               "carga horária mínima [VAR-138] e [VAR-138: formato: prática presencial, material em português, certificado], "
               "concluído [VAR-138: antes da utilização ou antes do recebimento definitivo].",
         vars_="VAR-138", wz="WZ-08",
         base="NE-024 nota 1",
         evid=f"{TR58} p.1: 'incluindo instalação, treinamento e garantia'; {TR23} p.11: 'Declaração de fornecimento de "
              f"treinamento de operação do equipamento;' (no corpus aparece como declaração de habilitação: ver M09)",
         obs="", status="INFERIDO"),
    dict(id="SET-13", tema="Garantia técnica do equipamento: serviços incluídos, local e prazos de atendimento, marco inicial, "
                           "equipamento substituto",
         documento="TR", origem="CK-P-13.1 a CK-P-13.8; CK-C-18.1",
         condicao="SE exigida garantia contratual do bem (WZ-29 = SIM)",
         expr=eq("WZ_29", "SIM"),
         ponto="TR: complementa o grupo GA-07 opção B (TR-5.6 a TR-5.17), preenchendo VAR-066 e VAR-067 e acrescentando os "
               "subitens de atendimento",
         texto="Durante a garantia estão incluídos, sem custo adicional, [VAR-139: serviços]. O atendimento será [VAR-139: no "
               "local de instalação] e começará em até [VAR-140] após a abertura do chamado. A garantia conta a partir de "
               "[VAR-141]. [Equipamento substituto: VAR-152, em complemento a TR-5.14.]",
         vars_="VAR-066; VAR-067; VAR-139; VAR-140; VAR-141; VAR-152; VAR-124", wz="WZ-29",
         base="NE-027; NE-029 (prazo de garantia justificado nos autos); NE-030 (assistência com deslocamento em distância "
              "compatível)",
         evid=f"{TR23} p.3: '5.8. A garantia abrange a manutenção corretiva (peças e mão de obra) sem ônus para o Contratante'; "
              f"'5.9.1. Caso o reparo ultrapasse esse prazo, a Contratada deverá disponibilizar veículo equivalente'",
         obs="Prazo de garantia por item (VAR-124, CK-P-13.1); acima de 12 meses exige justificativa (VAL-026).",
         status="INFERIDO"),
    dict(id="SET-14", tema="Assistência técnica, manutenção preventiva, calibração, suporte remoto e disponibilidade de peças",
         documento="AMBOS", origem="CK-P-14.1 a CK-P-14.7; CK-P-15.8; CK-P-16.4; CK-C-18.3",
         condicao="SE o checklist indicar assistência técnica especializada, manutenção preventiva, calibração ou suporte "
                  "(CK-P-14.1, CK-P-14.5, CK-P-14.6, CK-P-14.7 ou CK-C-18.3 = Sim)",
         expr=ou(sim(P, "14.1"), sim(P, "14.5"), sim(P, "14.6"), sim(P, "14.7"), sim(C, "18.3")),
         ponto="TR: complementa TR-5.9 a TR-5.12; ETP: ETP-06.01 (exigências de manutenção e assistência técnica, art. 18, "
               "§ 1º, VII)",
         texto="Durante a garantia, o Contratado fará manutenção preventiva [VAR-148: periodicidade], calibração ou verificação "
               "[VAR-148: periodicidade e comprovação] e prestará suporte [VAR-149: remoto, quando informado], com atendimento "
               "presencial em até [VAR-140].",
         vars_="VAR-148; VAR-149; VAR-140", wz="WZ-29; WZ-08",
         base="NE-009 nota 1 (art. 18, § 1º, VII: exigências de manutenção e assistência técnica); NE-030",
         evid=f"{TR58} p.16: '9.34.7. Declaração de que as peças de reposição estarão disponíveis no mercado para aquisição "
              f"futura, por um período não inferior a dez anos;' (declaração na habilitação: ver M09)",
         obs="Suporte remoto com acesso à rede da unidade aciona o alerta de TIC (VAL-001).", status="INFERIDO"),
    dict(id="SET-15", tema="Execução de instalação, treinamento ou assistência pelo fabricante ou por rede credenciada",
         documento="TR", origem="CK-P-11.2; CK-P-11.7; CK-P-12.8; CK-P-14.2; CK-P-18.6",
         condicao="SE a equipe administrativa decidir exigir fabricante ou rede credenciada (WZ-59 = SIM)",
         expr=eq("WZ_59", "SIM"),
         ponto="TR: seção 5 (execução) e, se for o caso, TR-4.15 (carta de solidariedade, WZ-21)",
         texto="[VAR-009: atividades] serão executadas pelo fabricante ou por empresa por ele credenciada, pelos motivos técnicos "
               "registrados no ETP.",
         vars_="VAR-009", wz="WZ-59; WZ-21",
         base="NE-014 (carta de solidariedade só em situação excepcional e motivada); TR-5.9 ('assistência técnica autorizada')",
         evid=f"{TR58} p.16: '9.34.8. Declaração de assistência técnica prestada diretamente pelo fabricante, seu representante "
              f"ou empresa autorizada por ele;'",
         obs="Restringe a competição: exige justificativa técnica (VAL-030).", status="INFERIDO"),
    dict(id="SET-16", tema="Software, licenças e atualizações",
         documento="AMBOS", origem="CK-P-15.3; CK-P-15.4; CK-P-15.6; CK-P-15.8",
         condicao="SE o equipamento depender de software ou licença (CK-P-15.3 = Sim)",
         expr=sim(P, "15.3"),
         ponto="TR: seção 4 (requisitos) e seção 5 (garantia); ETP: ETP-06.01",
         texto="O fornecimento inclui as licenças [VAR-142: módulos e tipo de licença] necessárias ao funcionamento integral do "
               "equipamento e [VAR-142: atualizações de software ou firmware durante a garantia, sem custo adicional].",
         vars_="VAR-142", wz="",
         base="NE-010 nota 2",
         evid=f"{ETP19} p.1: 'incluindo todos os componentes, softwares, treinamento, garantia e suporte técnico necessários à "
              f"sua operação'",
         obs="Se a solução for de TIC, o modelo AGU da base não se aplica (VAL-001).", status="INFERIDO"),
    dict(id="SET-17", tema="Preparação do local e requisitos de infraestrutura antes da entrega",
         documento="AMBOS", origem="CK-P-8.8; CK-P-9.1 a CK-P-9.7",
         condicao="SE o local precisar estar pronto antes da entrega (CK-P-8.8 = Sim) OU for exigido levantamento técnico do "
                  "fornecedor (CK-P-9.5 = Sim)",
         expr=ou(sim(P, "8.8"), sim(P, "9.5")),
         ponto="ETP: ETP-13.01 (providências prévias) e ETP-10.01 (obra ou serviço relacionado); TR: seção 5",
         texto="A entrega só ocorrerá com o local apto, nas condições [VAR-143]. [Se CK-P-9.5 = Sim: o Contratado apresentará "
               "levantamento técnico do local (site planning) com o conteúdo [VAR-143], no prazo definido pela equipe.]",
         vars_="VAR-143; VAR-105", wz="WZ-47; WZ-46",
         base="NE-024 nota 1",
         evid=f"{TR58} p.5: '5.2.2. A CONTRATADA não poderá entregar em seu local de destino nenhum equipamento, sistema, "
              f"software, partes, peças e acessórios sem que as dependências estejam aptas para o seu recebimento;'",
         obs="Obrigação da Administração (preparar o local) vai para ETP-13.01; obrigação do Contratado (levantamento técnico) "
             "vai para o TR.", status="INFERIDO"),
    dict(id="SET-18", tema="Desinstalação e retirada do equipamento existente",
         documento="AMBOS", origem="CK-P-20.1; CK-P-20.2; CK-P-20.3; CK-P-2.4",
         condicao="SE a equipe administrativa incluir a desinstalação como obrigação do fornecedor (WZ-58 = SIM)",
         expr=eq("WZ_58", "SIM"),
         ponto="TR: seção 5; ETP: ETP-06.01 e ETP-13.01",
         texto="O Contratado fará a desinstalação técnica e a retirada de [VAR-144: equipamento e local], com os procedimentos "
               "[VAR-144: descontaminação, retirada de fonte, drenagem, backup de dados, desenergização], antes da instalação do "
               "novo equipamento.",
         vars_="VAR-144", wz="WZ-58",
         base="NE-024 nota 1; NE-071 nota 1 (serviço associado ao bem)",
         evid="Sem evidência no corpus.",
         obs="Desinstalação é serviço associado: pode exigir tratamento de serviço (atestado, WZ-38; Fazenda municipal, NE-061).",
         status="INFERIDO"),
    dict(id="SET-19", tema="Manuais e documentos técnicos em português",
         documento="TR", origem="CK-P-16.6; CK-P-19.7",
         condicao="SE o checklist exigir manuais em português (CK-P-16.6 = Sim) E não houver Anexo I (no Anexo I a obrigação já "
                  "existe em TR-AI-4.1.1)",
         expr=e(sim(P, "16.6"), eq("WZ_43", "CONTRATO")),
         ponto="TR: seção 5",
         texto="O objeto será entregue acompanhado de [VAR-150: manuais de operação, manutenção e segurança e demais documentos "
               "técnicos], com versão em português.",
         vars_="VAR-150", wz="WZ-43",
         base="TR-AI-4.1.1 (texto do modelo no Anexo I: 'Entregar o objeto acompanhado do manual do usuário, com uma versão em "
              "português, e da relação da rede de assistência técnica autorizada')",
         evid=f"{TR190} p.2: 'Os objetos, quando couber, deverão estar acompanhados dos manuais do usuário, com uma versão em "
              f"português e da relação da rede de assistência técnica autorizada;'",
         obs="", status="INFERIDO"),
    dict(id="SET-20", tema="Recebimento: conferência, testes e aceitação definitiva",
         documento="TR", origem="CK-C-16.1; CK-C-16.2; CK-C-16.4; CK-P-19.1; CK-P-19.2; CK-P-19.4; CK-P-19.7; CK-P-11.5; "
                                "CK-P-12.6",
         condicao="SE o checklist listar controles de recebimento ou condicionar o recebimento definitivo a instalação, testes "
                  "ou treinamento",
         expr=ou(tem(ck(C, "16.1")), tem(ck(P, "19.1")), sim(P, "19.2"), sim(C, "16.4")),
         ponto="TR: complementa TR-8.1 a TR-8.3 (Recebimento)",
         texto="No recebimento provisório serão conferidos [VAR-146]. O recebimento definitivo ocorrerá após [VAR-146: "
               "instalação, testes e treinamento, quando exigidos] e a entrega de [VAR-145]. O produto será recusado quando "
               "[VAR-146: situações de recusa].",
         vars_="VAR-145; VAR-146; VAR-075", wz="WZ-34",
         base="TR-8.1 a TR-8.3; NE-026 nota 1 (regras de recebimento no TR Digital)",
         evid=f"{TR117} p.8: 'O processo de recebimento de OPME deverá incluir uma verificação detalhada da integridade das "
              f"embalagens, quantidade, especificação técnica e etiquetas de rastreabilidade.'",
         obs="", status="INFERIDO"),
    dict(id="SET-21", tema="Substituição de produto entregue (desvio de qualidade, embalagem danificada, quebra da cadeia de "
                           "frio, recall, fora da especificação)",
         documento="TR", origem="CK-C-18.2; CK-C-16.3",
         condicao="SE o checklist marcar situações de substituição (CK-C-18.2)",
         expr=tem(ck(C, "18.2")),
         ponto="TR: complementa TR-8.2 (rejeição e prazo de substituição, VAR-074)",
         texto="O Contratado substituirá, no prazo de [VAR-074], o produto entregue nas seguintes situações: [VAR-151].",
         vars_="VAR-151; VAR-074", wz="WZ-34",
         base="TR-8.2 (texto do modelo sobre rejeição e substituição)",
         evid="Sem evidência no corpus para a lista de situações (recall, desvio de qualidade).",
         obs="", status="INFERIDO"),
    dict(id="SET-22", tema="Logística reversa e recolhimento pelo fornecedor",
         documento="AMBOS", origem="CK-C-21.3; CK-P-21.2",
         condicao="SE o checklist indicar logística reversa ou recolhimento pelo fornecedor",
         expr=ou(e(tem(ck(C, "21.3")), nao_lista(C, "21.3", "Não")), sim(P, "21.2")),
         ponto="TR: seção 5 ou critérios de sustentabilidade (TR-4.1.1..TR-4.1.3); ETP: ETP-14.01",
         texto="O Contratado recolherá, sem ônus para o Contratante, [VAR-147: materiais e situações], dando a eles destinação "
               "ambientalmente adequada.",
         vars_="VAR-147; VAR-106", wz="WZ-48; WZ-17",
         base="NE-011 notas 7 e 8 (destinação ambiental dos resíduos; Lei 12.305/2010, Política Nacional de Resíduos Sólidos)",
         evid="Sem evidência no corpus.",
         obs="", status="INFERIDO"),
    dict(id="SET-23", tema="Atestado com garantia técnica já prestada a equipamento compatível (P25)",
         documento="TR", origem="CK-P-18.1; CK-P-18.3 (fatos de apoio); decisão na WZ-60",
         condicao="SE a equipe exigir que os atestados comprovem garantia já prestada a equipamento compatível (WZ-60 = SIM)",
         expr=eq("WZ_60", "SIM"),
         ponto="TR: qualificação técnica, depois das características dos atestados (TR-9.34 e subitens)",
         texto="Os atestados deverão comprovar também a prestação de garantia técnica a equipamento compatível com o objeto, "
               "pelo prazo mínimo de [VAR-161] meses, conforme justificativa constante do Estudo Técnico Preliminar.",
         vars_="VAR-161; VAR-162", wz="WZ-60; WZ-38",
         base="NE-071 (atestados sem limitação de tempo ou de época); resposta da P25 em 23/10/2026: a duração da garantia "
              "já prestada é permitida, com justificativa no ETP, e pode ser de 12 meses ou mais",
         evid=f"{TR23} p.11: '9.30.1.1. Venda, entrega, instalação e garantia mínima de 12 (doze) meses prestada ao "
              f"equipamento compatível com o objeto'; {TR58} p.16: '9.34.2.1. Venda, entrega, instalação e garantia mínima de "
              f"12 (doze) meses prestada ao equipamento'",
         obs="A exigência fica fora da VAL-029 (que barra período ou época do contrato atestado) e depende de justificativa "
             "no ETP (VAL-053) e de prazo de 12 meses ou mais (VAL-052).",
         status="INFERIDO"),
]


def main():
    pasta = Path(sys.argv[1])
    ids_m01 = {r["id"] for r in ler_csv(pasta / "M01_etp_campos.csv")}
    linhas = []
    for s in S:
        fonte = (f"Checklists (fonte principal): {s['origem']}. Base no modelo: {s['base']}. Evidência de redação no corpus: "
                 f"trecho e página citados em evidencia_corpus (EXTRAIDO). texto_proposto, condicao e ponto_insercao INFERIDOS.")
        linhas.append({"id": s["id"], "tema": s["tema"], "documento": s["documento"], "origem_checklist": s["origem"],
                       "condicao": s["condicao"], "condicao_expr": dumps(s["expr"]), "ponto_insercao": s["ponto"],
                       "texto_proposto": s["texto"], "variaveis": s["vars_"], "perguntas_wz": s["wz"],
                       "base_no_modelo": s["base"], "evidencia_corpus": s["evid"], "observacao": s["obs"], "fonte": fonte,
                       "status": s["status"]})
    gravar_csv(pasta / "M08_clausulas_setoriais.csv", COLS, linhas, preservar=())
    print(f"M08: {len(linhas)} cláusulas")


if __name__ == "__main__":
    main()
