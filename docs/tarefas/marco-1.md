# Marco 1: motor do TR, sem telas

**Objetivo:** funções puras em `src/motor/` que recebem o pacote de regras e as entradas de um processo e devolvem a minuta do TR, com cada trecho rastreável, mais a lista de alertas, bloqueios e pendências. Nada de tela, banco, login ou IA.

**Pré-requisito:** as matrizes da Fase 10 em `matrizes/v1/`. Elas trazem:

- as colunas `depende_de_expr` e `calculo_expr` (M04), `condicional_expr`, `preenche_expr` e `sugere_expr` (M11), `calculo_expr` e `calculo_ordem` (M05);
- o `M12_parametros.csv`;
- os cenários em `matrizes/v1/cenarios/` (C1 a C8, R1 e R2).

Se algo disso não estiver lá, pare e avise. O arquivo `correspondencia_processos.csv` nunca entra no repositório; se aparecer, pare e avise.

**Antes de começar:** leia `CLAUDE.md`, `docs/arquitetura.md` e `matrizes/v1/README.md`.

## Contrato

**Entrada (`EntradaProcesso`):**

- o pacote;
- as respostas do checklist, por ID `CK`;
- as respostas do wizard, por ID `WZ`;
- os itens, com os atributos do M05;
- as variáveis, por ID `VAR`;
- os dados da OM (fictícios nos testes).

**Saída (`Minuta`):**

- ID e hash do pacote;
- os blocos que entram, na ordem do modelo. Cada bloco tem: ID do M02, número recalculado, texto com as lacunas preenchidas (ou marcadas como `[[LACUNA VAR-xxx]]` quando faltar dado) e origem (a condição que o ligou e as respostas que ela usou);
- as cláusulas setoriais do M08, no ponto de inserção indicado;
- as lacunas pendentes;
- os alertas e bloqueios do M10;
- as perguntas do wizard ainda sem resposta.

## Passos

0. **Matrizes da Fase 10.** Já estão no ramo `marco-1`, num commit só. Trabalhe nesse ramo. Hoje `npm run compilar` falha antes de chegar às expressões: recusa o cabeçalho do M04, do M05 e do M11, por causa das colunas novas. Isso é esperado, e o pacote em `regras/` ainda é o do Marco 0. Comece pelo passo 1.

1. **Compilador e tipos.**
   - Atualize os cabeçalhos esperados: M04 ganha `depende_de_expr` e `calculo_expr`; M05 ganha `calculo_expr` e `calculo_ordem`; M11 ganha `condicional_expr`, `preenche_expr` e `sugere_expr`; entra o M12. Compile de novo e só então trate os erros de expressão.
   - Leia o `M12_parametros.csv` e inclua os parâmetros no pacote. O `valor` tem três formas: número, lista JSON (`[]`) ou texto (os marcadores de lei revogada). Valor que não se encaixa em nenhuma das três é erro. (Feito no passo 1. Hoje o tipo é lido da frase "Tipo do valor: …" na `fonte`; o agente das matrizes vai criar a coluna `tipo` no M12, e aí o compilador passa a ler a coluna.)
   - Acrescente `parametros.*` às variáveis conhecidas. Variável `parametros.x` sem linha no M12 é erro.
   - Operadores (decisão P31): `reduce`, `+`, `-`, `*`, `/` e `%` são aceitos **só** em `M04.calculo_expr` e `M05.calculo_expr`. Em qualquer outra coluna, são erro. As variáveis `accumulator` e `current` só valem dentro de `reduce`.
   - Contexto de item: dentro de `some`, `none` e `reduce` sobre itens, e no `calculo_expr` do M05, valem os atributos do item mais as respostas, as variáveis, os `parametros.*`, `itens_do_grupo` e `valor_unidade_disputa`, como descreve o README das matrizes. Fora disso, atributo de item solto é erro.
   - Ordem de cálculo: expressão do M05 que usa variável com `calculo_ordem` igual ou maior que a sua é erro.
   - Exporte para `src/motor/pacote/` os tipos do pacote, derivados dos esquemas Zod. Quem lê o arquivo do pacote é o script ou a aplicação, nunca o motor.
   - Atualize os testes do compilador com um caso de erro para cada regra nova.

2. **Avaliador de JSON Logic** em `src/motor/pacote/`. Escreva um avaliador próprio, só com os operadores permitidos, sem `eval` e sem biblioteca. Teste cada operador.
   - **Conta exata.** `+`, `-`, `*`, `/` e `%` não usam número de ponto flutuante. Converta cada número para decimal exato (inteiro grande com escala, feito no próprio avaliador) e compare também em decimal exato. Teste no limite: um grupo cuja soma dá exatamente o valor de `parametros.limite_exclusivo_me_epp` tem de dar EXCLUSIVO; um centavo acima, não.
   - Divisão por zero e conta com valor ausente devolvem ausente (`null`), nunca `NaN` ou `Infinity`. O que depender disso vira lacuna.
   - **Semântica igual à do simulador das matrizes** (Python), que gerou os cenários, e não à da biblioteca `json-logic-js`:
     - `==` e `!=` são estritos: `"30"` é diferente de `30`; números comparam por valor (`30` igual a `30.0`); `null` só é igual a `null`.
     - Falso para `!`, `!!`, `if`, `and` e `or`: `null`, `false`, `0`, `""` e `[]`. Todo o resto é verdadeiro, inclusive a lista não vazia.
     - `{"var": ""}` é o próprio elemento dentro de `some`, `none` e `reduce`; `{"var": ["X", padrão]}` devolve o padrão quando X falta. O compilador aceita as duas formas.
     - Escreva um teste para cada uma dessas regras, porque é aqui que dois avaliadores de JSON Logic costumam divergir.
   - O avaliador não arredonda por conta própria. Arredondamento só existe se a expressão o fizer (como a VAR-118 faz com `%`).

3. **Itens** (`src/motor/itens/`). Calcule os atributos derivados pelo `calculo_expr` do M05, na ordem de `calculo_ordem`, com os valores do M12. Exemplo: o tratamento ME/EPP (exclusivo, cota ou ampla) pelo valor estimado do item ou do grupo. Nenhum número de lei ou valor monetário no código. Cota igual a zero (decisão do Gabriel, 23/10/2026): já está na matriz da Fase 11 (VAR-160, VAR-113, VAR-118 e VAL-051). Retire do código o alerta provisório de cota zero; o alerta passa a vir só da VAL-051.

3b. **Matrizes da Fase 11.** Já estão no ramo `marco-1`. O compilador recusa os cabeçalhos novos. Ajuste:
   - M02 ganha `grupo_ativo_expr`; M11 ganha `leitura`, `revisao_expr` e `revisao_pergunta`; M12 ganha `tipo`. O compilador passa a ler o tipo da coluna `tipo` e deixa de ler a frase da `fonte`.
   - Aceite o checklist `COMPLEMENTO` e os IDs `CK-X-nn`.
   - Aceite as variáveis da leitura (`checklist.*` e os sufixos `_texto` e `_numero` de resposta de checklist). Variável fora dessa lista continua erro.
   - Aceite `false` como expressão (linha desligada: WZ-56, SET-01, VAL-027). Linha desligada nunca entra nem é oferecida.
   - Em `revisao_expr` e `grupo_ativo_expr`, só os operadores gerais, sem os de cálculo.
   - Retire dos testes o contorno da VAR-160: ela agora existe. Com isso, `npm run compilar` grava o pacote novo e o GitHub Actions volta a ficar verde. Confira.

4. **Do checklist para o wizard** (`src/motor/wizard/`).
   - `preenche_expr` preenche a resposta.
   - `sugere_expr` só gera uma sugestão marcada; quem decide é a equipe.
   - Se a equipe já respondeu de outro jeito, vale a resposta da equipe, e a diferença vira alerta.
   - Valor que não bate com o `tipo` do M05 não é convertido nem adivinhado: vira lacuna marcada e alerta. Caso real: a VAR-060 é NUMERO, mas a opção "Outro" da CK-C-12.1 e da CK-P-8.1 copia o texto livre ("20 dias"). Nesse caso a minuta mostra a lacuna e pede o número.

   - **Leitura e revisão (Fase 11, decisão 0009).** O checklist distribuído não muda; o sistema contorna. Para cada pergunta do M11:
     - `revisao_expr` verdadeira marca a resposta como **destaque** (o operador revisa; na tela, amarelo);
     - se a linha tiver `revisao_pergunta`, o motor devolve também uma **pergunta ao operador**, e a minuta fica bloqueada até a resposta;
     - a coluna `leitura` é texto para quem programa a leitura do Word no Marco 2; o motor não a executa.
   - **Dados da leitura.** As expressões usam o que a leitura do Word vai produzir: `checklist.consumo`, `checklist.permanentes`, `checklist.marcas_multiplas` (lista de IDs com mais de uma opção marcada) e os sufixos `_texto` e `_numero` (por exemplo `CK_C_12_1_numero`). Ponha esses campos no contrato de entrada (`src/motor/entrada.ts`), com a descrição do README das matrizes. Nos testes, preencha à mão.
   - **Complementos do operador.** As linhas `CK-X-01` a `CK-X-09` (`checklist = COMPLEMENTO`) são respondidas pelo operador no sistema e entram como qualquer resposta de checklist (`CK_X_03`).

5. **Wizard.** Calcule as perguntas habilitadas pela `depende_de_expr` e devolva as pendentes. Nunca escolha sozinho uma opção de pergunta marcada como `DECISAO_JURIDICA`.

6. **Montagem** (`src/motor/montagem/`).
   - **Quais blocos entram.** Um bloco entra pela sua `condicao_expr` e pelos `liga_expr` e `desliga_expr` do M04. Desligar vence ligar.
   - **Alternativas.** O grupo é ativo quando a `grupo_ativo_expr` do M02 é verdadeira (vazia = sempre ativo). Num grupo ativo, exatamente uma opção entra; nenhuma ou mais de uma vira bloqueio, listado em `bloqueios_grupo_alternativas` como nos cenários.
   - **O que fica fora.** Filho sem o pai não entra. Também ficam fora o cabeçalho do modelo, os separadores "OU" e tudo que o M02 marca como "não entra na minuta".
   - **Setoriais.** Entram as cláusulas do M08 cuja condição for verdadeira.
   - **Lacunas.** São preenchidas com variáveis e respostas. O que faltar fica marcado.
   - **Numeração.** É refeita depois das exclusões, nível a nível, com o Anexo I numerado à parte. Siga a P18 das matrizes para o "1.6.1" digitado no texto.

7. **Validação** (`src/motor/validacao/`). As regras do M10 com `condicao_expr` geram alertas ou bloqueios. As que não têm expressão (P27) ficam listadas como "conferência manual".

8. **Cenários de ouro** (`testes/cenarios/`). Os 8 cenários de `matrizes/v1/cenarios/` precisam dar exatamente os blocos, as cláusulas, os alertas e as pendências esperados. Os resultados esperados vêm de outra implementação (o simulador do agente das matrizes), então uma diferença aponta erro num dos dois. Não ajuste o código só para bater: investigue e diga de que lado está o erro.
   - Diferenças já conhecidas do simulador, que o agente das matrizes vai corrigir e reemitir os cenários: (a) ele trata valor ausente como 0 em contas e comparações; vale a regra desta tarefa (ausente dá ausente e vira lacuna); (b) ele não aplica "filho sem o pai não entra"; (c) ele não aplica "exatamente uma opção por grupo de alternativas". Nesses três pontos o motor segue esta tarefa. Se um cenário divergir só por um deles, registre como "simulador" e siga; não pare.
   - Os números do avaliador vêm do pacote como número do JavaScript. Converta para decimal exato pela forma escrita mais curta do número (`String(n)`), nunca pela representação binária.

9. **Reprodução** (R1 e R2). Compare a minuta com o TR real e classifique cada diferença em um de quatro tipos:
   - **motor**: erro do código;
   - **matriz**: regra que pode estar errada; vai para o Gabriel decidir;
   - **TR real**: erro já conhecido do documento, listado em `divergencias_conhecidas`;
   - **lacuna**: dado que só existe no processo real.

   Corrija só as do tipo "motor". Já decidido: no R1, os blocos TR-4.H08 e TR-4.41 (reserva de cota sem haver cota) são do tipo **TR real**.

10. **Simulação legível.** O script `scripts/simular-wizard.ts`, rodado com `npm run simular -- C1`, imprime a minuta do cenário em texto corrido. É assim que o Gabriel confere o resultado sem ler código.

## Critério de saída

- Os cenários C1 a C8 passam.
- Em R1 e R2, nenhuma diferença do tipo "motor", e todas as outras classificadas.
- `npm test`, `npm run lint`, `npm run typecheck` e o GitHub Actions passam.
- `npm run simular -- C1` imprime um TR legível.

## Não faça

- Telas, banco, login ou IA.
- Mudanças nas matrizes. Problema em matriz vai para a lista do Gabriel.
- Regra jurídica, número de lei ou valor monetário no código.

## Ao terminar

Mostre:

- o resultado dos 8 cenários e dos 2 casos de reprodução, com as diferenças classificadas;
- a saída de `npm run simular -- C1`;
- quantas regras ainda estão sem validação no M03 e no M04.

Explique em português simples o que foi feito e como conferir.
