# Auditoria das matrizes 01 e 02 (Fase 8)

Arquivos auditados: `Matriz/01_Matriz_TR_AGU_Aquisicoes.md` e `Matriz/02_Matriz_ETP_Digital_Lei14133.md` (rascunhos, nível 4 da hierarquia de fontes). Referências: M02 (texto literal do modelo DEZ/2025), M01 (campos do ETP Digital), M03 (notas), M07 (normas). Contagens geradas por `scripts/f8_auditoria.py`; conclusões INFERIDAS. Os desvios principais também estão no M09 (DV-31 a DV-34).

## Conclusão

As duas matrizes servem como inventário de assuntos, não como fonte do sistema. A matriz 01 não copia o texto do modelo na maior parte das linhas e não registra as notas explicativas; a matriz 02 mistura o ETP Digital com práticas de um TR específico (numeração do TR 117/2025), marca como obrigatórias seções que a lei não exige e deixa de marcar uma que exige, e cita normas que não estão na base nem foram conferidas. As matrizes v1 substituem as duas: M02 e M03 no lugar da matriz 01; M01, M06 e M11 no lugar da matriz 02.

## Matriz 01: TR AGU

- Linhas de campo (tabelas com '#'): 97.
- Classificação do 'Conteúdo Modelo AGU' contra o texto literal do M02: LITERAL 18; LITERAL_COM_CORTES 16; PARAFRASE 13; SEM_CORRESPONDENCIA 6; SEM_TEXTO_DO_MODELO 44.
- Blocos do M02 (sem notas e separadores) cujo texto aparece em alguma linha: 34 de 474. As demais linhas descrevem blocos sem copiar o texto ('Bloco completo sobre procedimento de amostra', 'Blocos extensos sobre seguro-garantia...'), o que impede usar a matriz como fonte literal.
- Ocorrências da palavra 'nota': 0. O modelo DEZ/2025 tem 102 notas explicativas (M03). Ver DV-31.
- Ocorrências de '~' (estimativa): 13, inclusive no resumo estatístico final ('~47% texto fixo'). Ver DV-33.
- Arquivo-fonte declarado: `media_1792606488039_644bd1c3.docx`, sem hash; 30 dos 35 intervalos 'Linhas' batem pelo título com o docx DEZ/2025 e 5 pedem leitura (logs/f0_conferencias.txt, seção 4). Ver DV-32.
- Tipo da linha contra a formatação do modelo (só nas linhas com texto casado):
  - linha 48 (1.3.2): tipo TF, mas TR-1.4 é VERMELHO_ITALICO (condição no M02: SE bens de consumo (NE-006 remete ao art. 20 da Lei 14.133/2021, sobre itens de consumo, e)
  - linha 86 (4.1.1): tipo TF, mas TR-4.1 é VERMELHO_ITALICO (condição no M02: Sempre, salvo justificativa nos autos para não adotar critérios de sustentabilidade (NE-01)
- Pontos lidos linha a linha:
  - Linha 48 (1.3.2, bem de luxo): marcada como texto fixo 'sempre presente'; no modelo o item é vermelho itálico e a NE-006 o liga ao bem de consumo (TR-1.4).
  - Linha 130 (4.7.1, cota de ME/EPP): 'reserva de 25%'. O modelo e a NE-022 falam em cota de até 25%; o Decreto 8.538/2015, art. 8º, também ('até vinte e cinco por cento', conferido no planalto.gov.br).
  - Linhas 54 a 56 (vigência): o texto da opção B ('prorrogável por até 10 anos') e o da opção C ('improrrogável') não estão no corpo do modelo com essa redação; as opções reais são TR-1.6/TR-1.7 e TR-1.8.
  - Linhas 158, 181, 197, 204 e 212: trechos que não correspondem a nenhum bloco do modelo (prazos e percentuais reescritos).

## Matriz 02: ETP Digital

- Seções: 15 (1. Informações Básicas & Órgão Demandante; 2. Descrição da Necessidade da Contratação (Inciso I, art. 18, § 1º); 3. Área Requisitante & Equipe de Planejamento; 4. Requisitos da Contratação (Inciso III, art. 18, § 1º); 5. Levantamento de Mercado & Justificativa da Escolha da Solução (Inciso V); 6. Descrição da Solução como um Todo (Inciso VII, art. 18, § 1º); 7. Estimativa das Quantidades & Memória de Cálculo (Inciso IV, art. 18, § 1º); 8. Estimativa do Valor da Contratação (Inciso VI, art. 18, § 1º); 9. Justificativa para Parcelamento ou Não da Solução (Inciso VIII, art. 18, § 1º); 10. Contratações Correlatas e/ou Interdependentes (Inciso XI, art. 18, § 1º); 11. Alinhamento com o Plano de Contratações Anual - PCA (Inciso II, art. 18, § 1º); 12. Justificativas Técnicas Específicas / Qualificação & Amostra; 13. Providências a Serem Adotadas Previamente (Inciso X, art. 18, § 1º); 14. Possíveis Impactos Ambientais & Logística Sustentável (Inciso XII, art. 18, § 1º); 15. Posicionamento Conclusivo sobre a Viabilidade (Inciso XIII, art. 18, § 1º)).
- A seção 12 da matriz é 'Justificativas Técnicas Específicas / Qualificação & Amostra'; no ETP Digital e nos ETPs do corpus a seção 12 é 'Resultados Pretendidos' ou 'Benefícios a serem alcançados com a contratação' (M01 ETP-12.01; P07). A seção 16 (Responsáveis) não existe na matriz; as assinaturas estão em 15.3.
- O campo 3.3 'Equipe de Planejamento da Contratação' não é campo do ETP Digital nos ETPs do corpus (M01 tem ETP-03.01 e ETP-03.02) e aponta para 'Cláusula 22 do TR', que não existe no modelo.
- Seções com linha marcada 'Obrigatório': 1, 2, 3, 6, 7, 8, 15. O art. 18, § 2º, exige os incisos I, IV, VI, VIII e XIII (seções 2, 7, 8, 9 e 15 do ETP Digital). A matriz não marca a seção 9 (parcelamento, inciso VIII) e marca a 6 (solução, inciso VII), a 1 e a 3 (dados de identificação) e o 6.3 (índice de reajuste, que não é elemento do ETP). O M01 marca os cinco incisos (teste 6).
- A linha 62 (4.1) fixa 'Validade mínima de 50% na data da entrega' como 'regra padrão hospitalar militar'. A decisão de 22/10/2026 (P21) é sem valor sugerido: a validade vem da CK-C-14.2, item a item.
- Referências a itens do TR que não existem no modelo DEZ/2025 (7 linhas); a numeração é a do TR 117/2025:
  - linha 44 (2.3 Classificação do Bem (Comum x Especial)): 1.2.1
  - linha 54 (3.3 Equipe de Planejamento da Contratação): 22
  - linha 63 (4.2 Conformidade Regulatória Sanitária (ANVISA)): 9.2.1, 9.2.3
  - linha 64 (4.3 Rastreabilidade e Etiquetas de Implante): 5.16.3
  - linha 66 (4.5 Regime de Comodato e Instrumental de Apoio): 1.11, 1.12
  - linha 89 (6.2 Enquadramento como Fornecimento Contínuo): 1.6.1
  - linha 91 (6.4 Regime de Consignação (se aplicável)): 5.4.3
- Coluna 'Base Normativa' contra a base (norma e artigo citados no modelo AGU ou nas notas, ou conferidos em fonte oficial; a conferência é no nível do artigo, sem parágrafo, inciso ou alínea):
  - linha 29 (1.1) 'Lei 14.133/21, art. 12, VI': Lei nº 14.133/2021: norma na base, mas art. 12 não citado no modelo nem conferido
  - linha 30 (1.2) 'IN 58/22, art. 8º': Instrução Normativa SEGES/ME nº 58/2022: na base
  - linha 31 (1.3) 'IN 58/22, art. 8º': Instrução Normativa SEGES/ME nº 58/2022: na base
  - linha 52 (3.1) 'IN 58/22, art. 8º, III': Instrução Normativa SEGES/ME nº 58/2022: na base
  - linha 53 (3.2) 'IN 58/22, art. 8º, III': Instrução Normativa SEGES/ME nº 58/2022: na base
  - linha 54 (3.3) 'Lei 14.133/21, art. 7º': Lei nº 14.133/2021: na base
  - linha 62 (4.1) 'Boas Práticas / ANVISA': 'Boas Práticas / ANVISA': sem norma identificável
  - linha 63 (4.2) 'Lei 6.360/76, RDC 185/01, RDC 751/22': Lei nº 6.360/1976: na base; RDC Anvisa nº 185: fora da base e não conferida; RDC Anvisa nº 751: fora da base e não conferida
  - linha 64 (4.3) 'RDC ANVISA / Normas EB': 'RDC ANVISA': sem norma identificável; 'Normas EB': sem norma identificável
  - linha 65 (4.4) 'RDC ANVISA / Boas Práticas': 'RDC ANVISA': sem norma identificável; 'Boas Práticas': sem norma identificável
  - linha 66 (4.5) 'Prática Setorial de Saúde': 'Prática Setorial de Saúde': sem norma identificável
  - linha 67 (4.6) 'Lei 14.133/21, art. 67, § 4º': Lei nº 14.133/2021: na base
  - linha 75 (5.1) 'IN 58/22, art. 9º': Instrução Normativa SEGES/ME nº 58/2022: na base
  - linha 76 (5.2) 'IN 58/22, art. 9º, III, "a"': Instrução Normativa SEGES/ME nº 58/2022: na base
  - linha 77 (5.3) 'IN SEGES 65/2021': Instrução Normativa SEGES/ME nº 65/2021: na base
  - linha 88 (6.1) 'Lei 14.133/21, art. 18, § 1º, VII': Lei nº 14.133/2021: na base
  - linha 89 (6.2) 'Lei 14.133/21, art. 6º, XV c/c arts. 106 e 107': Lei nº 14.133/2021: na base
  - linha 90 (6.3) 'Lei 14.133/21, art. 25, § 7º': Lei nº 14.133/2021: na base
  - linha 91 (6.4) 'Ajuste SINIEF 02/2024': 'Ajuste SINIEF 02/2024': sem norma identificável
  - linha 123 (9.1) 'Art. 40, V, "b" c/c art. 47, § 1º': Lei nº 14.133/2021 (lei não nomeada; presumida): na base
  - linha 124 (9.2) 'Art. 40, § 3º c/c Súmula TCU 247': Lei nº 14.133/2021 (lei não nomeada; presumida): na base
  - linha 125 (9.3) 'Art. 48, § 3º, II da Lei 14.133/21': Lei nº 14.133/2021: norma na base, mas art. 48 não citado no modelo nem conferido
  - linha 133 (10.1) 'Art. 18, § 1º, XI': Lei nº 14.133/2021 (lei não nomeada; presumida): na base
  - linha 141 (11.1) 'IN SEGES 58/22 e Decreto 10.947/22': Instrução Normativa SEGES/ME nº 58/2022: na base; Decreto nº 10.947/2022: fora da base e não conferida
  - linha 142 (11.2) 'Decreto 10.947/22': Decreto nº 10.947/2022: fora da base e não conferida
  - linha 143 (11.3) 'IN 58/22': Instrução Normativa SEGES/ME nº 58/2022: na base
  - linha 151 (12.1) 'Art. 67 da Lei 14.133/21': Lei nº 14.133/2021: na base
  - linha 152 (12.2) 'Art. 41, II da Lei 14.133/21': Lei nº 14.133/2021: na base
  - linha 160 (13.1) 'Art. 18, § 1º, X': Lei nº 14.133/2021 (lei não nomeada; presumida): na base
  - linha 168 (14.1) 'IN 01/2010 SLTI/MP e Dec 7.746/12': Instrução Normativa SLTI/MP nº 1/2010: fora da base e não conferida; 'Dec 7.746/12': sem norma identificável
  - linha 169 (14.2) 'Protocolo de Montreal / Conama 267': 'Protocolo de Montreal': sem norma identificável; 'Conama 267': sem norma identificável
- Linha 44 (2.3) fundamenta 'bem comum' no Decreto 10.024/2019, e a linha 168 (14.1) cita a IN SLTI/MP 01/2010: normas do regime anterior, situação não conferida (DV-34; VAL-004).
- O fecho da matriz afirma que 'mais de 80% do Termo de Referência é preenchido automaticamente'. Não há contagem que sustente o número; o M06 classifica a origem de cada bloco do M02 e é a medida a usar.

## O que foi aproveitado

- Da matriz 01: a legenda de tipos (TF, EU, IA, OP, TB), mantida no M02 com regra explícita por formatação.
- Da matriz 02: as colunas 'regra de preenchimento e anti-alucinação' e 'transposição para o TR', que viraram M01.regra_anti_alucinacao, M01.destino_tr e o M06.
- Da matriz 02, como tema de cláusula setorial (M08), não como texto: comodato (4.5), rastreabilidade (4.3), logística e transporte (4.4) e regime de consignação (6.4, sem a norma citada, que não foi conferida).
