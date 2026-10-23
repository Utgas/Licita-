# Escopo inicial: gerador de ETP e TR

> Documento histórico, de 20/10/2026, copiado do documento "Escopo Inicial: Gerador de ETP e TR" (claude.ai). Onde divergir de `docs/arquitetura.md`, vale a arquitetura. As principais mudanças depois dele: o checklist técnico virou a entrada principal no lugar do DFD; o rascunho fica guardado enquanto o processo está aberto e é apagado depois; a hospedagem é Vercel e Supabase; a primeira versão não usa IA.

## Visão do produto

O produto é um assistente interno de redação. Ele transforma o relatório de demanda em minuta de ETP e de TR no modelo AGU. A minuta passa por revisão humana e depois é transcrita no ETP Digital e no TR Digital do Compras.gov.br.

**O que é**

- Assistente de redação da fase preparatória (art. 18 da Lei 14.133/2021).
- Gerador de minuta em PDF para ler, imprimir, reler e circular internamente.
- Organizado campo a campo, na mesma ordem das telas do ETP Digital e do TR Digital, para a cópia ser direta.

**O que não é**

- Não é o documento oficial. O oficial é o que fica no Compras.gov.br (IN SEGES 58/2022 e IN SEGES 81/2022).
- Não é fonte de preço. A estimativa vem da pesquisa de preços (IN SEGES 65/2021).
- Não substitui a revisão do requisitante, da equipe de planejamento e da CJU.

## Usuários

O piloto roda em uma única OM, com quatro perfis.

| Perfil | O que faz no sistema | O que vê |
| --- | --- | --- |
| Requisitante | Responde ao checklist técnico (no escopo inicial: envia o DFD ou relatório) | Os próprios processos |
| Elaborador | Gera, edita e exporta a minuta | Os processos em que atua |
| Revisor ou chefe de seção | Revisa e libera a minuta para o Compras.gov.br | Os processos da seção |
| Administrador | Mantém modelos e base normativa, consulta a auditoria | Todos os registros, nunca o conteúdo |

## Fluxo de ponta a ponta

O documento passa por oito etapas, e a revisão humana é a única porta de saída.

1. Entrada: checklist técnico (no escopo inicial, DFD ou relatório).
2. Anonimização: tira dados pessoais antes de qualquer envio à IA (v2).
3. Redação: por regras na v0 e na v1; com IA na v2, sempre com trecho de origem.
4. Wizard: completa as lacunas e as decisões jurídicas.
5. Validador: regras automáticas.
6. Revisão humana: edição na tela.
7. Saída: PDF e texto por campo; registro e hash gravados.
8. Compras.gov.br: ETP Digital e TR Digital, colados à mão.

## Escopo do MVP (original)

O MVP cobria um único tipo de objeto, de ponta a ponta. Na prática, o modelo AGU escolhido (aquisições, exceto TIC) cobre compras de consumo e de permanentes; a arquitetura mantém o recorte de uma versão por vez (v0 só TR).

**Fora, por enquanto**

- Serviços com dedicação exclusiva de mão de obra, TIC (IN SGD 94/2022), obras e serviços de engenharia.
- DFD, mapa de riscos, edital e minuta de contrato.
- Pesquisa de preços.
- Integração automática com o Compras.gov.br.
- PDF escaneado.
- Uso por outras OMs ou comercialização.

## Base normativa

O texto da minuta só pode vir de três fontes: o modelo AGU vigente, a base normativa curada e o que o usuário informou.

| Norma ou fonte | Papel no sistema |
| --- | --- |
| Lei 14.133/2021, art. 6º, XXIII | Elementos obrigatórios do TR |
| Lei 14.133/2021, art. 18, §§ 1º e 2º | Os 13 elementos do ETP e os 5 obrigatórios |
| Lei 14.133/2021, arts. 40 e 47 | Parcelamento ou não da solução |
| IN SEGES 58/2022 | Regras do ETP e do ETP Digital |
| IN SEGES 81/2022 | Regras do TR e do TR Digital |
| IN SEGES 65/2021 | Pesquisa de preços, só como referência |
| Modelos AGU e suas notas explicativas | Texto-base de cada seção |
| Normas internas do EB e da OM | A levantar |

## Regras anti-alucinação

1. Cada parágrafo gerado mostra a fonte que o sustenta. Sem fonte, o campo volta vazio, com a marca "não consta".
2. Nenhuma citação de acórdão, súmula ou artigo fora da base curada.
3. Números nunca são gerados. Quantidades, prazos e valores vêm do usuário, e o sistema confere se o texto bate com a fonte.
4. As cláusulas padrão do modelo AGU entram como texto fixo.
5. Desvio do modelo AGU exige justificativa escrita e fundamentada, que vai para o documento.
6. Um validador roda antes do PDF.
7. Regra nova só entra depois de passar no banco de testes com casos reais.

## Riscos principais

| Risco | Consequência | Mitigação |
| --- | --- | --- |
| Revisor confia demais na minuta | Erro chega à CJU ou ao edital | Origem visível, campos vazios quando falta dado, revisão obrigatória por seção |
| Uso de dado real sem autorização | Problema disciplinar e encerramento do projeto | Autorização formal antes de qualquer dado real |
| Fundamento inventado | Parecer da CJU com ressalva | Base curada e validador |
| Modelo AGU atualizado e sistema não | Minuta fora do padrão | Versionamento e checagem periódica no site da AGU |
| Movimentação do responsável para outra OM | Sistema sem dono | Documentação e um segundo responsável desde o início |
| Virar produto sem análise | Questionamento ético ou disciplinar | Consulta jurídica antes de qualquer comercialização |
