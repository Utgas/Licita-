# Perguntas abertas: Licita+, Matrizes v1

Arquivo vivo. Cada fase acrescenta itens. Cada item traz a situação, a opção que recomendo e o motivo. Conflitos entre fontes de níveis diferentes também entram aqui (seção 3 do prompt).

Situação de cada item:

- `ABERTA`: precisa de decisão ou de arquivo seu.
- `ADOTADA PROVISORIAMENTE`: sigo com a recomendação até você dizer o contrário.
- `RESOLVIDA`: você decidiu; a decisão está registrada no item.

---

## Fase 0: inventário

### P01. Nome de arquivo com nomes de pessoas (RESOLVIDA)

- **Decisão:** renomear. Feito na cópia de trabalho: o arquivo agora é `ETP exemplos/Outro-ETP160322_000058_2025 Controlado ASSINADO.pdf`, e o M00 e os scripts usam esse nome.
- **Pendente do seu lado:** renomear também na sua pasta `Documentos`, para os caminhos da coluna `fonte` baterem com a base.

### P02. Três TRs feitos sobre versões anteriores do modelo AGU (RESOLVIDA)

- **Decisão:** as versões NOV/2024 e ABR/2025 não entram na base. Na Fase 6, só os TRs 23/2026 e 58/2026 são comparados com o DEZ/2025. Os TRs 117/2025, 140/2025 e 190/2025 entram só no M08, como evidência de prática, sem classificar diferença como desvio.

### P03. Valores fora do domínio previsto no M00 (RESOLVIDA)

- **Decisão:** aceitos `srp = NA` para documentos que não são contratação e `papel_srp = ?` para os ETPs 58/2025, 330/2025 e 67/2026.

### P04. ETP 19/2026 incompleto (RESOLVIDA)

- **Decisão:** o arquivo não será substituído. As seções que caem nas páginas ausentes (6, 7, 12, 13, 14 e o título da 15) ficam como `não lido` em definitivo no M01, nunca como omitidas.
- **Por que não faz falta:** o ETP 19/2026 não tem TR par na base, então só pesa na estatística de 5 seções do M01, que passa a contar 7 ETPs nessas seções. O dado mais útil do arquivo, a divergência entre o campo Valor (R$ 3.317,00) e o texto da seção 8 (R$ 331.765,00), está numa página lida e foi conferido na imagem, não só no OCR.

### P05. Não existe a pasta `Documentos/Normas` (RESOLVIDA, opção a)

- **Decisão:** na Fase 5, situação e dispositivo de cada norma são conferidos só em planalto.gov.br, in.gov.br e gov.br, com URL e data.
- **Limite já encontrado:** a ferramenta de leitura só alcança os primeiros 80.878 caracteres da página da Lei 14.133/2021 no Planalto (até o art. 36). Artigos posteriores ficam `A_VERIFICAR` até eu achar outra página oficial que os traga ou até o PDF oficial entrar na base. Por isso tirei do M01 uma citação ao art. 40, § 2º, que eu não consegui conferir.

### P06. Numeração das seções do ETP Digital (RESOLVIDA)

- **Decisão:** aceita. Seção identificada pelo nome e pelo ID estável `ETP-SS.CC`; número impresso tratado como posicional.

### P07. Nome da seção 12 do ETP (RESOLVIDA)

- **Decisão:** aceita. "Resultados Pretendidos" é o nome principal; "Benefícios a serem alcançados com a contratação" fica como variante.

### P08. Pares ETP e TR (RESOLVIDA)

- **Decisão:** aceita. A Fase 4 testa a derivação no par 117/2025 e usa 67/2026 x 23/2026 como caso de divergência ETP x TR.

### P09. Gerenciador da IRP 134/2025 (ABERTA)

- **Situação:** a resposta veio com o marcador sem preencher ("[SIM ou NÃO: o TR 190/2025 é da IRP 134/2025]"). Sigo tratando o TR 190/2025 como não confirmado.
- **Recomendo:** responder SIM ou NÃO.
- **Por quê:** se for, a base ganha um conjunto completo de gerenciador e participantes (TR 190/2025 e ETPs 99/2025, 151/2025 e 801/2025), o melhor caso de teste para a WZ-11 e para a consolidação das quantidades por órgão (TR-1.1.1.TAB1 a TAB3).
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** o dono do projeto não sabe. Continua aberta; o TR 190/2025 segue como não confirmado.

### P10. DFD do processo do par 117/2025 (RESOLVIDA, 23/10/2026)

- **Situação (22/10/2026):** entraram três DFDs (18/2026, 710/2025 e o da PMPV) e os dois checklists técnicos. As origens que dependiam de DFD foram refeitas: o checklist passou a ser a entrada da área requisitante (M11) e as linhas deixaram de ser `A_VERIFICAR`. Nenhum DFD novo é do processo PROC-02, então a cadeia DFD, ETP e TR continua sem caso completo.
- **Recomendo:** incluir, anonimizado, o DFD (ou o checklist preenchido) do processo PROC-02.
- **Por quê:** é o único processo com ETP e TR na base; com a peça de origem, o M06 testaria a cadeia inteira.
- **Atenção:** o DFD da PMPV traz nomes e CPF de pessoas. Nada disso foi copiado para as matrizes, mas o arquivo da base deveria ser anonimizado.
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** seguir sem o DFD do PROC-02. O Marco 3 testa só a derivação do ETP para o TR.

### P11. Arquivo-fonte da matriz 01 (RESOLVIDA)

- **Decisão:** aceita. O docx DEZ/2025 é tratado como fonte da matriz 01, e a troca entra na auditoria (Fase 8).

---

## Fases 1 a 3: M01 a M05

### P12. Realce ciano como marca de conteúdo de registro de preços (ADOTADA PROVISORIAMENTE)

- **Situação:** o modelo tem realce em 20 blocos: ciano em 13, amarelo em 5, verde em 2. Os 13 em ciano tratam de registro de preços (TR-1.1.1 e suas 3 tabelas, TR-9.H03, TR-9.4, TR-9.4.1, TR-10.5 a TR-10.5.4, TR-11.4). Nenhuma nota explica as cores.
- **Recomendo:** usar o ciano só como indício, com status `INFERIDO` nas condições "SE registro de preços", e não usar amarelo nem verde em regra nenhuma.
- **Por quê:** o padrão vale para 13 de 13 blocos, mas sem nota da AGU continua sendo inferência. O amarelo aparece, entre outros, nos itens TR-AI-5.5 a TR-AI-5.6, cuja nota (NE-098) cita a ON AGU 98, de 8 de agosto de 2025; parece marca de alteração recente, não de conteúdo.

### P13. Órgão participante de IRP: o sistema gera só o ETP? (RESOLVIDA)

- **Resposta (21/10/2026):** a OM conduz cerca de 140 pregões por ano, e só parte deles tem participação externa. Nesses, o participante faz o ETP e não faz TR; o TR é compilado pela OM gerenciadora. Às vezes o participante manda um TR pronto.
- **Consequência no desenho:** o fluxo principal é o do pregão conduzido pela OM. Na WZ-11, PARTICIPANTE gera só o ETP, e a pergunta deixou de ser `A_VERIFICAR`. TR pronto enviado por participante entra no processo do gerenciador como fonte de dados (itens, quantidades, endereço), não como texto: a minuta continua saindo do modelo AGU carregado, porque esses TRs podem vir de versão anterior do modelo, como os três TRs de 2025 da base.

### P14. Anexo I em contratação de pequeno valor sem fornecimento contínuo (ADOTADA PROVISORIAMENTE)

- **Situação:** o Anexo I tem três redações de vigência (GA-12) e três de extinção (GA-13). A vigência A (TR-AI-2.1, art. 105) não tem nota e serve a qualquer contrato por escopo. A extinção A (TR-AI-5.1 a TR-AI-5.3.2) tem nota que a destina à compra com entrega imediata (NE-096). As opções B e C são para pequeno valor de fornecimento contínuo e para emergência. Nenhuma nota cobre o pequeno valor (art. 95, I) sem fornecimento contínuo e sem entrega imediata, por exemplo uma entrega parcelada em quatro meses.
- **Recomendo:** usar a opção A nos dois grupos, com status `INFERIDO` e alerta na minuta.
- **Por quê:** a extinção A trata de contrato que termina quando as obrigações são cumpridas, o que descreve um contrato por escopo; B e C exigem fornecimento contínuo ou emergência, que o caso não tem.

### P15. Estimativa de valor sem redação indicada: técnica e preço e contratação direta (ADOTADA PROVISORIAMENTE)

- **Situação:** as notas da seção 10 só indicam a redação para menor preço (TR-10.1, NE-074 nota 3; TR-10.3 com sigilo, NE-077) e para maior desconto (TR-10.2, NE-076). O critério técnica e preço, que o item 9.1 oferece, e a contratação direta não têm redação indicada. O modelo também não traz critérios de pontuação técnica.
- **Recomendo:** (a) nesses casos, usar TR-10.1, ou TR-10.3 com orçamento sigiloso, com status `INFERIDO`; (b) no técnica e preço, o wizard avisa que os critérios de pontuação precisam ser escritos pelo usuário, e o sistema não os gera.
- **Por quê:** TR-10.1 só declara o valor estimado, o que serve a qualquer critério. Gerar critérios de pontuação sem fonte seria preencher por dedução.

### P16. Obrigações do Decreto 12.174/2024 no Anexo I (RESOLVIDA na Fase 10 e CONFIRMADA em 23/10/2026)

- **Situação:** os itens TR-AI-4.1.22 a TR-AI-4.1.26 estão em vermelho itálico. A NE-095 só diz que vêm do art. 2º do Decreto 12.174/2024, sem dizer quando suprimi-los. A WZ-51 decide a inclusão.
- **Conferência (23/10/2026):** texto no planalto.gov.br (https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/d12174.htm). Sem nota de revogação. O art. 1º, caput, trata das "garantias trabalhistas a serem observadas na execução dos contratos administrativos no âmbito da administração pública federal direta, autárquica e fundacional". O art. 2º, caput, diz: "Os contratos administrativos conterão cláusulas que disponham sobre:" (I proteção ao trabalho; II trabalho escravo e infantil; III denúncias de discriminação, violência e assédio; IV responsabilidade solidária por subcontratada). O art. 3º é o que se restringe a serviços contínuos com dedicação exclusiva de mão de obra.
- **Alteração depois de 2024:** o Decreto 12.926, de 13/04/2026 (https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12926.htm, DOU de 14/04/2026), mudou o art. 1º, parágrafo único (antes "arts. 2º e 3º", agora só "art. 2º" se aplica às obras e serviços de engenharia do art. 46 da Lei 14.133), o art. 3º e o art. 5º, § 3º. O art. 2º ficou igual.
- **Decisão:** a WZ-51 fica com padrão SIM, status `INFERIDO` e passa a exigir justificativa para NAO. O decreto não restringe o art. 2º a serviços, então compras também estão no alcance pelo texto.
- **O que continua sendo leitura minha:** o Anexo I só aparece quando não há termo de contrato (WZ-43 diferente de CONTRATO). Tratar o instrumento substitutivo como "contrato administrativo" para o art. 2º é inferência; o decreto não fala dele. Se a assessoria jurídica entender diferente, basta mudar o padrão da WZ-51.
- **Repositório auxiliar:** o arquivo do decreto no ctresb/leis (commit 15eb09b, `federal/decretos/2024/dec-12174-2024-09-11.md`) tem `versao_texto: "original"` e não foi usado para o conteúdo.
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** confirmada. WZ-51 com padrão SIM; resposta NAO exige justificativa.

### P17. Textos prontos que estão dentro das notas, fora do corpo do modelo (RESOLVIDA)

- **Situação:** três notas trazem texto para inserir no TR: NE-016 nota 3 (subcontratação obrigatória de ME/EPP, com itens numerados 4.24 a 4.29), NE-071 nota 4 (atestados de potencial subcontratado) e NE-094 nota 3 (cláusula de LGPD, que remete ao modelo de serviços, ausente da base). O M02 cobre só o corpo do modelo, então esses textos estão só no M03.
- **Recomendo:** na revisão do M02, acrescentar blocos condicionais para a NE-016 nota 3 e a NE-071 nota 4, copiados literalmente da nota, com IDs novos (ex.: `TR-NE016.01`) e numeração recalculada na minuta. Deixar a LGPD de fora até o modelo de serviços entrar na base.
- **Por quê:** sem esses blocos, o wizard pergunta (WZ-08, WZ-22) mas não tem o texto que a própria AGU manda inserir. A LGPD dependeria de texto que eu não li.
- **Decisão (21/10/2026):** aceita. O M02 ganhou TR-NE016.01 a TR-NE016.08 (WZ-22 = SIM_EXIGIDA_ME_EPP) e TR-NE071.01 (WZ-38 = ATESTADO_POTENCIAL_SUBCONTRATADO), com formatação `NOTA_EXPLICATIVA`.

### P18. Inconsistências internas do modelo AGU (ADOTADA PROVISORIAMENTE)

- **Situação:**
  1. A NE-099 manda usar "a redação do item 12.4", que não existe no Anexo I. A nota está ancorada no TR-AI-5.7, que trata do art. 75, VIII.
  2. A NE-069, nota 2, remete a uma nota sobre "vistoria", que não existe neste modelo.
  3. A NE-016, nota 3, numera os itens sugeridos como 4.24 a 4.29, números que o corpo já usa (garantia da contratação).
  4. NE-057 e NE-058 têm texto idêntico, ancorado no mesmo trecho.
  5. NE-089 e NE-090 tratam do mesmo item (TR-AI-3.1.10).
  6. No parágrafo 108, o número "1.6.1" está digitado no texto, e o Word exibe "1.7. 1.6.1". O bloco TR-1.7 guarda o texto literal, com "1.6.1".
- **Recomendo:** manter o texto literal no M02 e no M03 (regra 3); mapear a NE-099 para o TR-AI-5.7 (`INFERIDO`); registrar as duplicatas; na minuta, tratar o "1.6.1" digitado como numeração e não imprimi-lo, regra aplicada só a esse parágrafo.
- **Por quê:** a regra 3 proíbe corrigir o texto da AGU, mas o "1.6.1" é numeração manual, não conteúdo; imprimi-lo geraria item com dois números. Os seis pontos entram na auditoria (Fase 8).

### P19. Seção adicional do ETP, "Justificativas pontuais" (RESOLVIDA, 23/10/2026)

- **Situação:** só o ETP 117/2025 tem essa seção, numerada 12, o que desloca as seguintes. Não sei se o ETP Digital permite criar seção livre ou se era um recurso que deixou de existir. No M01 ela é o campo ETP-90.01, `A_VERIFICAR`.
- **Recomendo:** conferir nas telas do ETP Digital. Se for seção livre, manter ETP-90.01 como opcional e sem texto padrão; se não existir, retirar.
- **Por quê:** o sistema não deve propor seção que o ETP Digital não aceita.
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** o ETP Digital aceita a seção. A ETP-90.01 fica opcional e sem texto padrão (só entra se o requisitante escrever) e deixou de ser `A_VERIFICAR`.

### P20. Formatação que não basta para decidir a inclusão (ADOTADA PROVISORIAMENTE)

- **Situação:** (a) TR-5.3, TR-5.4, TR-7.2.4.1 e TR-7.2.4.3 a TR-7.2.4.6 estão inteiros em vermelho itálico, mas o conteúdo cabe em qualquer compra (aviso de atraso, local de entrega, multas). Marquei como `EU` (variável e sempre incluído), não `OP`. O TR-6.5 (reunião inicial), também inteiro em vermelho itálico e sem nota, ficou opcional (WZ-31). (b) O TR-ASSIN.03 ("Identificação e assinatura do servidor (ou equipe) responsável") está em preto, portanto invariável pela regra 4, mas funciona como rótulo a preencher.
- **Recomendo:** aceitar (a). Em (b), manter o texto em preto e acrescentar abaixo dele o cargo de cada responsável (VAR-098), sem substituir o rótulo.
- **Por quê:** em (a), a formatação diz que o texto é variável, não que é opcional, e toda compra tem prazo e local de entrega e multas compensatórias (art. 156, citado na NE-036). Em (b), a regra 4 manda seguir a formatação.

### P21. Validade mínima na entrega sem valor padrão (RESOLVIDA)

- **Situação:** o item 5.4.1 deixa a validade mínima em aberto. No corpus aparecem 50% e 75% do prazo total, e o ETP 99/2025 se contradiz ("até no máximo 75% de vida útil" e "mínimo de 75%", DV-19).
- **Decisão (21/10/2026 e 22/10/2026):** sem valor sugerido. A validade vem da CK-C-14.2, item a item, com as opções do próprio checklist: 12 meses, 75% do prazo total, dois terços do prazo total ou outro critério (VAR-117). O wizard não propõe número; item perecível sem validade bloqueia (VAL-007) e "Outro critério" sem descrição também (VAL-008). A matriz 02 fixava 50% como padrão; isso foi descartado (auditoria).

---

## Fases 4 a 9 e checklists técnicos (22/10/2026)

### P22. Decisões por item (ajuste 1) (ADOTADA PROVISORIAMENTE)

- **Situação:** o tratamento de ME/EPP, o grupo, a amostra, a marca e a validade passaram a ser atributos de cada item (VAR-011 e VAR-112 a VAR-124). Quatro escolhas de desenho não estão escritas no modelo nem nas notas.
- **Recomendo:**
  1. Unidade de disputa: o item isolado, ou o grupo inteiro (o grupo é "considerado como item", NE-022). O Decreto 8.538/2015, conferido no planalto.gov.br, fala em "itens ou lotes" de até R$ 80.000,00 (art. 6º).
  2. Quantidade da cota: parte inteira de quantidade × percentual / 100; se der zero em algum item da unidade, a unidade fica AMPLA (não há cota de fração).
  3. Exceção sobre item que seria EXCLUSIVO: permitida só com a hipótese do art. 10 do decreto e alerta (VAL-017, `A_VERIFICAR`).
  4. Validade: coluna por item (VAR-117); a VAR-065 só existe quando todos os perecíveis têm o mesmo critério.
- **Por quê:** são as leituras que reproduzem a NE-003 e a NE-022 sem inventar número. A 2 e a 3 merecem confirmação da assessoria jurídica.
- **Cota calculada em zero (decisão 0008, 23/10/2026):** confirmado o item 2. A VAR-160 (`cota_calculada`, ordem 4) guarda a parte inteira de quantidade x VAR-057 / 100 de todo item; a VAR-113 (ordem 5) só dá COTA quando todo item da unidade tem cota maior que zero; senão AMPLA, e a VAL-051 avisa. A VAR-118 (ordem 6) copia a VAR-160 quando o item é COTA. Não há ciclo: 160 antes de 113, 113 antes de 118. Item sem valor unitário fica sem valor da unidade e sem tratamento (regra do valor ausente).

### P23. Especificação das matrizes M06 a M10 e achados da seção 5 (RESOLVIDA, 23/10/2026)

- **Situação:** o texto original do prompt não está mais disponível nesta sessão; o `attachment.txt` reenviado em 22/10/2026 é a lista de tarefas, não o prompt. As colunas do M06 ao M10 e a lista dos achados da seção 5 foram reconstruídas a partir do registro das Fases 0 a 3 (logs/f0_conferencias.txt e perguntas P01 a P11). O README descreve o que foi reconstruído.
- **Recomendo:** reenviar o prompt original, ou só as seções que descrevem M06 a M10 e a seção 5, para eu conferir colunas e achados.
- **Por quê:** o teste 8 depende da lista exata de achados; hoje ele usa a lista reconstruída (10 achados).
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** fechada pelo gestor. O prompt original não será reenviado; a especificação reconstruída no README passa a ser a oficial, e o teste 8 continua com a lista de 10 achados.

### P24. Comodato numa aquisição (RESOLVIDA, 23/10/2026: fora do sistema por enquanto)

- **Situação:** o checklist de consumo tem uma seção inteira sobre comodato (10.1 a 10.11) e o TR 117/2025 usa "consignação com comodato", mas o modelo AGU e as notas não tratam do assunto. Criei a WZ-56 e o SET-01, ambos `A_VERIFICAR`.
- **Recomendo:** a assessoria jurídica decidir se o comodato entra como obrigação acessória da compra (cláusula no TR, como no SET-01) ou como instrumento próprio.
- **Por quê:** o custo do equipamento vai embutido no preço do material e afeta a competição; é decisão jurídica, não técnica.
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** o comodato fica fora do sistema por enquanto. Um estudo jurídico futuro pode trazer uma pergunta sim/não com justificativa padrão com lacunas, sujeita à validação do dono do projeto.
- **Como ficou desligado, sem apagar linhas:** a condição passou a ser `false` e o motivo está no texto da própria linha, que começa por "DESLIGADA": WZ-56 (`depende_de` e `depende_de_expr`; a pergunta não é oferecida), SET-01 (`condicao` e `condicao_expr`; a cláusula nunca entra) e VAL-027 (o alerta de comodato sem decisão perderia o sentido). No M11, as perguntas 10.1 a 10.11 do consumo viraram `SO_CONTROLE`, sem destino nem expressão, com a regra antiga guardada no texto (S21). A SET-12 deixou de ler a CK-C-10.8. Para religar, basta trocar `false` pela condição anterior, escrita no texto.

### P25. Atestado que exige "garantia mínima de 12 meses prestada" (RESOLVIDA, 23/10/2026)

- **Situação:** os TRs 23/2026 e 58/2026 exigem atestado de contrato com garantia mínima de 12 meses prestada (DV-09). A NE-071 veda limitação de tempo ou de época nos atestados; não está claro se a duração da garantia atestada entra na vedação.
- **Recomendo:** a assessoria jurídica responder. Até lá, o sistema não oferece essa característica de atestado.
- **Por quê:** se for vedada, a exigência restringe a habilitação sem base; se não for, falta a justificativa técnica no ETP.
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** pendente de esclarecimento. Continua aberta; o sistema não oferece essa característica de atestado (nenhuma opção da WZ-38 nem bloco a gera).
- **Resposta (decisão 0008, respostas seguintes, 23/10/2026):** permitido, com justificativa no ETP; a garantia exigida pode ser de 12 meses ou mais.
- **Como entrou:** pergunta nova WZ-60 (só quando a WZ-38 tem ATESTADOS), cláusula SET-23 com o prazo na VAR-161, justificativa na VAR-162, VAL-052 (prazo vazio ou menor que 12 meses, PAR-13) e VAL-053 (sem justificativa). A VAL-029 continua barrando o período ou a época do contrato atestado ("últimos", "período mínimo" sem tratar de garantia) e deixou de barrar a duração da garantia já prestada. DV-09 atualizado.

### P26. Leitura por máquina do checklist preenchido no Word (ABERTA para o Marco 2; checklist congelado, decisão 0009)

- **Como seria a leitura (sem código):**
  1. Abrir o docx preenchido e percorrer os parágrafos e as tabelas na ordem do documento, como o `ck_ler.py` faz com o modelo em branco.
  2. Identificar cada pergunta pelo número digitado no começo do parágrafo ("14.2.") e conferir o enunciado com o do M11 (texto literal). Enunciado diferente indica outra versão do checklist (VAL-036).
  3. Ler as opções: o "☐" trocado por "☒", "☑" ou "X" marca a opção; a opção cujo marcador continua "☐" está desmarcada.
  4. Ler a resposta na tabela de uma célula que vem logo depois de "Resposta:" e, nas tabelas com rótulo (ex.: "Itens | Faixa de temperatura"), cada célula pelo rótulo.
  5. Nas perguntas por item (por_item = S), ligar a resposta aos itens da tabela de itens pelo número do item.
  6. Gravar as respostas como `CK_C_14_2` e similares (convenção do jlogic.py) e mostrar tudo ao usuário para confirmação antes de gerar a minuta.
- **O que torna a leitura incerta:**
  - marca diferente das previstas (realce, negrito, opção apagada, "x" no meio do texto, ✓);
  - duas opções marcadas numa pergunta UNICA, ou nenhuma numa pergunta obrigatória;
  - resposta escrita fora da caixa (no parágrafo seguinte, em comentário ou na caixa da pergunta de baixo);
  - "Outro" marcado sem especificação; opção com lacuna dentro do texto ("Outro: ______ meses");
  - pergunta renumerada, apagada ou com o enunciado editado; numeração automática do Word aplicada por cima da digitada;
  - controle de alterações não aceito (texto inserido e apagado convivem no arquivo);
  - itens citados por descrição, faixa ("1 a 5") ou "todos", em vez de número;
  - checklist impresso e escaneado (só OCR, sem estrutura).
- **Recomendo:** cada incerteza vira pendência na leitura (VAL-037), e a pendência bloqueia a geração até o usuário confirmar. Na revisão do checklist, trocar "☐" por caixa de seleção do Word e cada resposta por controle de conteúdo com marca igual ao ID do M11 (sugestoes_checklist.md, S19).
- **Por quê:** com âncoras de texto, a leitura funciona enquanto o usuário não mexe no formulário; com controles de conteúdo, a âncora deixa de depender do texto.
- **Decisão 0009 (23/10/2026):** o Word distribuído não muda. A leitura segue a coluna `leitura` do M11; o que fica incerto é destacado pela `revisao_expr` e, quando muda a minuta, vira pergunta ao operador (`revisao_pergunta`), com a VAL-037 bloqueando a geração até a resposta. O que o motor precisa oferecer para isso está na P32.

### P27. Condições que não cabem em JSON Logic (ADOTADA PROVISORIAMENTE)

- **Situação:** o M02, o M04, o M08 e o M10 têm as condições em JSON Logic (condicao_expr, liga_expr, desliga_expr). Ficaram fora:
  1. Nove regras do M10 que comparam texto livre, contam itens por grupo ou comparam a minuta com o modelo ou o ETP com o TR: VAL-002, VAL-003, VAL-014, VAL-034, VAL-035, VAL-042, VAL-043, VAL-044 e VAL-045 (condicao_expr vazia).
  2. Ligações de trecho dentro de um bloco, que o JSON Logic de bloco inteiro não representa: WZ-08 (trecho opcional de TR-1.1), WZ-24 (linha de cota em TR-1.1.TAB1), WZ-33 (trecho entre colchetes de TR-7.2.4.7), WZ-40 (trecho de TR-12.1 e colunas de valor de TR-1.1.TAB1) e WZ-43 (trecho de assistência técnica de TR-AI-4.1.1). Os "Preenche ..." do M04 preenchem lacunas e não são condição.
  3. Atributos calculados antes da avaliação: tratamento_me_epp e valor_unidade_disputa (soma por grupo), tic (lista de classes da OM) e a WZ-50 (contagem de unidades de disputa).
- **Recomendo:** (1) e (3) como funções do sistema que rodam antes do JSON Logic e gravam o resultado em atributo; (2) dividir esses blocos em sub-blocos com ID próprio numa versão 2 do M02.
- **Por quê:** o JSON Logic padrão não tem agregação por grupo nem comparação de textos; forçar operadores próprios tiraria a portabilidade das expressões.
- **Fase 10 (23/10/2026):** o item 3 saiu daqui. tratamento_me_epp, valor_unidade_disputa, quantidade_cota, perecivel, tic e as derivadas do M04 (inclusive a WZ-50) ganharam `calculo_expr`, com os operadores padrão `reduce`, `+`, `*`, `-`, `/` e `%`, que estão fora da lista da Fase 10 (P31). Os itens 1 e 2 continuam.

### P28. Lista de classes de TIC para o alerta de escopo (RESOLVIDA, 23/10/2026)

- **Situação:** o VAL-001 usa o atributo tic de cada item, calculado pela classe ou PDM do DFD (VAR-153, VAR-154). Não há na base lista oficial de classes de TIC.
- **Recomendo:** a OM manter a lista (classes e PDM que ela trata como TIC) como parâmetro do sistema; até lá, o alerta usa só as perguntas 15.3 e 15.5 do checklist de permanentes.
- **Por quê:** inventar a lista seria preencher por dedução.
- **Fase 10:** a lista virou o parâmetro `classes_tic` (M12, PAR-12), vazio até a OM cadastrar; com a lista vazia todo item sai com tic = N.
- **Lote 1 de respostas (decisão 0008, 23/10/2026):** não é prioridade; processos de TIC são raros na OM. O PAR-12 fica vazio e a VAL-001 usa só a 15.3 e a 15.5 do checklist de permanentes. A VAR-154 continua calculada (sai tic = N com a lista vazia) para quando a lista existir.

### P29. Origem CHECKLIST no M05 e variáveis novas (ADOTADA PROVISORIAMENTE)

- **Situação:** o domínio de origem do M05 era DFD, WIZARD, SISTEMA e PESQUISA_PRECOS. Com o checklist como entrada, acrescentei CHECKLIST e criei 31 variáveis (VAR-125 a VAR-155): 28 para o texto das cláusulas setoriais e 3 atributos de item (classe_pdm, tic, categoria).
- **Recomendo:** aceitar. A VAR-011 (tabela de itens) continua com origem DFD, porque o DFD do Compras.gov é a fonte mais estruturada; o checklist só anexa a tabela.
- **Por quê:** cada lacuna das cláusulas precisa de variável com origem e validação, como as do modelo AGU.

### P30. Checklist e M11 (INFORMATIVA)

- **Situação:** o M11 foi feito sobre as versões dos docx cujo SHA-256 está no README. Qualquer mudança no checklist exige refazer o M11 (rodar `ck_ler.py` e `ck_gerar_M11.py`). As sugestões para a revisão estão em sugestoes_checklist.md.
- **Decisão 0009 (23/10/2026):** a versão distribuída (hashes no README) fica congelada; o M11 mapeia só ela. As sugestões S01 a S21 viraram regras de leitura, destaques, perguntas ao operador e complementos (sugestoes_checklist.md, linha "No sistema"). Uma versão nova do checklist gera M11 e pacote novos.

### P31. Fase 10: o que ficou fora da lista de operadores e as convenções que o compilador e o motor precisam aceitar (RESOLVIDA, 23/10/2026)

- **Operadores fora da lista:** `reduce`, `+`, `*`, `-`, `/` e `%`, só em `M04.calculo_expr` e `M05.calculo_expr`. Motivo: somar quantidade x valor unitário dos itens do grupo (VAR-119), tirar a parte inteira de quantidade x VAR-057 / 100 (VAR-118), contar grupos e itens isolados (WZ-50), listar os itens com amostra (VAR-049) e achar a validade comum aos perecíveis (VAR-065). Não usei `>=`, `<` nem `all`: troquei por `<=` e `>` com os lados invertidos e por `none` com a condição negada. Todos são operadores do JSON Logic padrão; nenhum é próprio.
- **Variáveis novas:** `itens_do_grupo` (itens com o mesmo rótulo de grupo, ou só o próprio item), `current.<atributo>` e `accumulator` (dentro do `reduce`), `parametros.<nome>` com nome do M12, e `CK_x_n` dentro do item, que é a resposta ligada àquele item quando a pergunta é por item.
- **Contexto de item:** cada elemento de `itens` traz também as variáveis globais (WZ, CK, VAR, parametros e metadados). Sem isso, `some` e `none` não conseguem comparar um atributo do item com um parâmetro, porque o JSON Logic padrão só enxerga o próprio elemento dentro do laço. A VAL-017, a VAL-025 e a VAL-026 dependem disso.
- **Números dentro de expressão:** 0 e 1 só como valor inicial e passo de contagem em `reduce`; no M11, número que traduz opção da própria pergunta ('36 meses' vira 36, '30 dias' vira 30). O "0" da WZ-12 é resposta (nenhum participante). O resto vem do M12.
- **Colunas novas fora do pedido:** `M04.calculo_expr` (derivadas) e `M05.calculo_ordem` (ordem de cálculo). Sem a primeira, a WZ-57, que depende da WZ-09, não teria valor para avaliar; sem a segunda, o motor teria de descobrir a ordem lendo as expressões.
- **O que o M11 não permitiu traduzir:** 41 destinos WZ sem expressão, 11 deles por serem perguntas derivadas (o valor vem do atributo de item). Os outros 30 ficaram de fora porque a regra não diz o valor (ex.: CK-C-6.2, que admite inexigibilidade ou marca indicada), porque a WZ é decisão jurídica (WZ-57, WZ-58) ou porque a resposta da WZ é composta (WZ-15, WZ-27, WZ-34: prazo mais termo inicial). Lista linha a linha em `logs/f10_expr.txt`. Nove perguntas PREENCHE ou SUGERE ficaram sem expressão, também com motivo no log.
- **Ponto para decidir:** a VAL-029 procura "período mínimo" dentro da VAR-085, que é LISTA. Com contribuições do checklist (CK-C-17.4, CK-P-18.3, CK-P-18.4), a VAR-085 vira lista, e `in` passa a comparar elemento inteiro, não trecho. A regra só funciona como foi escrita se a VAR-085 for o texto final editado pela equipe.
- **Recomendo:** (1) ajustar o compilador para aceitar os seis operadores só nas duas colunas de cálculo, as variáveis acima e o contexto de item; (2) manter o contexto de item como contrato do motor (README, "JSON Logic"); (3) decidir se a VAR-085 passa a TEXTO ou se a VAL-029 lê o texto final.
- **Por quê:** sem esses operadores, o motor teria de calcular ME/EPP e quantidade da cota em código, que é exatamente o que o projeto proíbe.
- **Decisão (23/10/2026):** os seis operadores ficam aceitos só em `M04.calculo_expr` e `M05.calculo_expr`, e o contexto de item fica como está no README. A VAR-085 continua lista: a VAL-029 passou a usar `some` sobre a `VAR_085` e procura "período mínimo", "Período mínimo", "últimos" e "Últimos" em cada item (`{"var": ""}` é o próprio item da lista). O PAR-05 passou a valor numérico (30, dias corridos); a VAL-020 e a condicional da CK-C-12.2 comparam a VAR-060, que recebe o prazo da CK-C-12.1 em número.

### P32. Fase 11: o que o motor e o compilador precisam oferecer para a leitura do checklist e as regras novas (RESPONDIDA em parte, 23/10/2026)

- **Leitura do Word (função do motor, não expressão):**
  1. `CK_x_numero`: número lido do texto escrito no "Outro" do prazo de entrega (CK-C-12.1 e CK-P-8.1), quando o texto é número seguido de "dias" (ex.: "45 dias" vira 45); qualquer outra coisa deixa vazio (S20). Sem isso, a VAR-060 fica vazia no "Outro" e a pergunta ao operador resolve.
  2. `checklist.marcas_multiplas`: lista dos IDs de pergunta de uma opção (UNICA e SIM_NAO) que vieram com duas ou mais marcas; a resposta fica vazia (S05).
  3. `checklist.resposta_unica_por_item`: lista dos IDs de pergunta por item (CK-C-14.1, CK-C-14.2, CK-P-13.1) respondidas uma vez só, sem indicar itens; a leitura aplica a resposta a todos os itens do checklist (S07).
  4. `checklist.divergencias_leitura`: lista dos IDs em que a leitura achou diferença que a expressão não compara, hoje o nome do responsável no cabeçalho e na tabela 1.4 (S03).
  5. Detector de nome de pessoa: não existe; por isso as perguntas "Quem..." ficam destacadas sempre que respondidas (S08). Um detector reduziria os destaques.
- **Compilador:** aceitar as colunas novas (`M11.leitura`, `M11.revisao_expr`, `M11.revisao_pergunta`, `M02.grupo_ativo_expr`, `M12.tipo`), o checklist `COMPLEMENTO` e os IDs `CK-X-01` a `CK-X-09` (variáveis `CK_X_01` e seguintes), o sufixo `_numero` ao lado do `_texto`, os metadados acima (já cabem em `checklist.*`), a VAR-160 e a VAL-051, e `false` como expressão de condição desligada. Em `revisao_expr`, só operadores gerais.
- **Grupo de alternativas ativo (`M02.grupo_ativo_expr`):** coluna nova, preenchida nas linhas que têm grupo, com o mesmo valor em todas as linhas do grupo. GA-03 só vale com WZ-49 = SIM (PCA detalhado); GA-11 a GA-13 só quando WZ-43 é diferente de CONTRATO (Anexo I); os demais grupos valem sempre. Num grupo ativo, exatamente uma opção entra; nenhuma ou mais de uma é bloqueio.
- **Ordem de avaliação:** `revisao_expr` é avaliada no fim, com os mesmos dados das validações do M10 (depois do preenchimento do M11 e do cálculo do M05), porque a S09 lê o valor da unidade de disputa.
- **Outros "Outro" que ainda copiam texto para variável NUMERO:** CK-C-16.3 e CK-P-19.5 (VAR-074), CK-P-19.3 (VAR-075), CK-P-13.7 (VAR-067) e "Outro: ______ meses" da CK-P-13.1 (garantia). A S20 cobre só o prazo de entrega; até decisão, o motor trata esses casos como lacuna com alerta (passo 4 do Marco 1). Estender a leitura `_numero` a eles depende do dono do projeto.
- **Recomendo:** implementar 1 a 4 na leitura do Marco 2 e ajustar o compilador agora, no Marco 1.
- **Por quê:** ler número em texto livre e comparar nomes não cabem em JSON Logic sem operador novo, e a decisão 0009 manda deixar a regra no M11, não no código.
- **Respostas de 23/10/2026:** (1) o sistema lê o número escrito em todos os "Outro" de prazo e de garantia: CK-C-16.3, CK-P-19.5, CK-P-19.3, CK-P-13.7 e CK-P-13.1 passaram a usar `CK_x_numero`, com destaque e pergunta quando o número não é legível; na CK-P-19.3, a opção "30 dias" (corridos) não vira dias úteis e também vira pergunta. (2) As perguntas "Quem..." ficam destacadas sempre; princípio geral: na dúvida, destacar para o operador. Continuam com o motor e o compilador: a leitura dos itens 1 a 4 e o ajuste do compilador.

### P33. Validação no repositório (INFORMATIVA)

- **Decisão (23/10/2026):** as colunas `validacao` e `comentario_validacao` do M03 e do M04 passam a ser mantidas no repositório (`matrizes/v1/`). Toda entrega nova parte delas.
- **Como fica:** o `rodar_fases_4_9.sh` recebe a pasta `matrizes/v1` do repositório como 4º argumento; o `f12_validacao_repo.py` copia as duas colunas para os CSV locais antes de regenerar, os geradores preservam essas colunas, e o teste compara linha a linha com o repositório. Linha validada no repositório que deixou de existir para a execução com erro.

### P34. Revisão do checklist: o que só destaca e o que bloqueia (A CONFIRMAR com o dono do projeto)

- **Decisão do gestor (23/10/2026, Fase 13):** pergunta sem resposta só fica destacada; a pergunta ao operador, que bloqueia a minuta, só aparece com dúvida que muda a minuta: duas marcas em pergunta de uma opção, "Outro" sem número legível, resposta única para vários itens em regra por item, e grupos de itens que parecem trocados com a seção 11 (CK-C-8.2). A falta de resposta que decide um bloco já aparece como pergunta pendente do wizard.
- **Como entrou:** coluna nova `M11.revisao_pergunta_expr` (75 perguntas). `revisao_expr` continua sendo o destaque (260 perguntas). `revisao_pergunta` só existe onde há `revisao_pergunta_expr`. A VAL-037 passou a descrever o bloqueio só pela pergunta que bloqueia.
- **Ponto para confirmar:** divergências com regra de prevalência (13.5 x 20.1, 5.5/5.6 x 6.1, cabeçalho x seção 1) e contradições que não mudam a minuta (12.2, 7.2, 11.2, 11.4) ficaram só com destaque, porque a regra já diz qual resposta vale ou porque a resposta não vai ao texto. Se o dono do projeto quiser que essas também bloqueiem, basta acrescentar a condição na `revisao_pergunta_expr`.

### P35. Numeração da linha de cota reservada na tabela do item 1.1 (ABERTA)

- **O que o modelo mostra:** a linha "Idem ao Item 1 – Cota reservada para ME/EPP em XX,XX%" logo abaixo do item 1, com o número 2.
- **O que adotei (INFERIDO):** a linha de cota entra logo abaixo do item de origem, com o número seguinte, e as linhas seguintes são renumeradas; a linha de origem fica com a quantidade principal (quantidade menos a cota, VAR-174). As referências a número de item no TR (amostras, padrões) passam a usar o número da tabela.
- **Pergunta:** no Compras.gov.br a OM numera assim (cota logo abaixo, renumerando) ou mantém o número do DFD e põe as cotas no fim da lista? A resposta muda a `tabela_colunas` do TR-1.1.TAB1 e a VAR-049.

### P36. Marcadores do texto das cláusulas do M08 (ABERTA)

- **Problema:** o texto proposto do M08 usa `[VAR-xxx: dica]` e, em algumas cláusulas, a mesma variável aparece em vários marcadores com partes diferentes (SET-09: três vezes a VAR-131; SET-12: cinco vezes a VAR-138; SET-11, SET-13, SET-14 e SET-20 também). O motor preenche cada marcador com o valor inteiro da variável, e o texto repete. Há ainda trechos entre colchetes que não são variável ("[na proposta ou na entrega]" na SET-07; "[Para permanentes: ...]" na SET-02; "[Se CK-P-9.5 = Sim: ...]" na SET-17).
- **Opções:** (a) dar ao M08 um mapa como o `lacunas_mapa` do M02, com campo por marcador e trechos opcionais com condição; (b) reescrever essas cláusulas com uma variável por marcador e criar as variáveis que faltam. Nos dois casos a redação continua INFERIDO e passa pela revisão.

### P37. Escolhas por padrão no texto e pendências fora das lacunas (INFORMATIVA)

- **Escolhas por padrão (INFERIDO, a confirmar na revisão):** TR-1.7 remete ao Estudo Técnico Preliminar (o sistema gera o ETP; nota técnica ou texto próprio são trocados pela equipe); TR-AI-3.1.8.1 sem prazo informado fica com "1 (um) mês" (NE-087); TR-9.4.1 com tabela no TR aponta o item 1.1 (onde está a tabela de preços).
- **Fica com a equipe (fonte null, motivo no mapa):** margem de preferência (TR-4.42), artigo e lei das autorizações (TR-9.14 e TR-9.35), até a norma estar conferida no M07; texto da subcontratação de ME/EPP da nota 3 da NE-016; número e ano do certame no Anexo II.
- **Texto do modelo:** o TR-1.7 começa com "1.6.1" dentro do próprio texto (numeração do modelo); a tabela do item 1.1 não tem coluna nem linha de grupo para itens agrupados.
