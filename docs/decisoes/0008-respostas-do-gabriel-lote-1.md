# 0008. Respostas do Gabriel às perguntas abertas (lote 1)

- Data: 23/10/2026
- Situação: aceita. Dadas pelo Gabriel no chat de gestão do projeto.

## Contexto

As perguntas abertas das matrizes (`matrizes/v1/perguntas_abertas.md`) e as decisões do plano (`docs/arquitetura.md`) passam a ser respondidas pelo Gabriel no chat, em lotes. Este registro guarda as respostas até o agente das matrizes levá-las para as matrizes. As matrizes continuam sendo alteradas só pelo agente das matrizes, porque cada entrega dele substitui `matrizes/v1/` inteira.

## Respostas

| Tema | Resposta | Efeito |
| --- | --- | --- |
| Decisão 0006 (testes do compilador) | Aprovada | Nenhum |
| TR 23/2026 com blocos de cota sem cota (TR-4.H08, TR-4.41) | Erro do TR real | R1 classifica a diferença como "TR real"; entra em `divergencias_conhecidas` |
| Cota calculada em zero (VAR-118) | Item sem cota, em ampla participação, com alerta | Regra nova na matriz (VAR-113 e uma validação) |
| P16 (Decreto 12.174 no Anexo I, WZ-51) | Confirmada a decisão do agente: padrão SIM, NÃO exige justificativa | P16 fechada |
| P09 (TR 190/2025 e IRP 134/2025) | Não sabe | Continua aberta; TR 190/2025 segue como não confirmado |
| P10 (DFD do PROC-02) | Seguir sem | Fechada; o Marco 3 testa só a derivação ETP para TR |
| P19 (seção "Justificativas pontuais" no ETP) | O ETP Digital aceita | ETP-90.01 opcional, sem texto padrão |
| P24 (comodato) | Fora do sistema por enquanto | WZ-56 e SET-01 não são oferecidos. Estudo jurídico futuro pode trazer uma pergunta sim/não com justificativa padrão, sujeita à validação do Gabriel |
| P25 (atestado com garantia mínima prestada) | Pendente de esclarecimento | Continua aberta |
| P28 (classes de TIC) | Não é prioridade; processos de TIC são raros na OM | PAR-12 fica vazio; o alerta usa só as perguntas do checklist |
| Prazo de expurgo | 30 dias após "concluído" | Trava do Marco 2 resolvida |
| Formato do checklist | Formulário no sistema e Word | Trava do Marco 2 resolvida |

## Respostas seguintes (23/10/2026)

| Tema | Resposta | Efeito |
| --- | --- | --- |
| P25 (atestado com garantia mínima prestada) | Permitido, com justificativa no ETP. A garantia exigida pode ser de 12 meses ou mais | A característica passa a ser oferecida, com justificativa obrigatória; a VAL-029 não pode bloqueá-la |
| P32.1 ("Outro" que deveria ser número) | O sistema lê o número escrito; o que não conseguir ler fica destacado | Mesma regra da S20 para CK-C-16.3, CK-P-19.5, CK-P-19.3, CK-P-13.7 e CK-P-13.1 |
| P32.2 (perguntas "Quem…") | Destacar sempre | Princípio geral: na dúvida, destacar para o operador |
| M03, lote 3 (NE-003 a NE-017, 10 regras CONDICAO) | OK, seguindo o parecer do gestor | `validacao = OK` nas 10 linhas, com o comentário de que a aceitação seguiu o parecer |

A validação do M03 e do M04 agora fica no repositório. Toda entrega nova do agente das matrizes precisa manter as colunas `validacao` e `comentario_validacao` como estão aqui.

## Reprodução do R1 e do R2 (23/10/2026)

| Tema | Resposta | Efeito |
| --- | --- | --- |
| Declaração de bem que não é de luxo (TR-1.4) | Não entra para bens permanentes; o Decreto 10.818/2021 trata de bens de consumo | Condição do TR-1.4 só para consumo; o TR 23 vira divergência "TR real" |
| TR-11.3, TR-9.33.1 e TR-9.4 mantidos pelo TR real sem a situação que os justifica | Erro do TR real | Divergências registradas no M09 |
| Garantia do TR 23 com redação própria | Diferença de redação do TR real; o sistema usa o modelo e a SET-13 | Divergência "TR real" |
| Reserva de cota sem cota no TR 58 | Erro do TR real, como no TR 23 | Divergência registrada no M09 para o TR 58 |
| SET-13 quando há garantia do bem | Mantida sempre que houver garantia | Nenhum |
| Revisão do checklist (P34) | Pergunta sem resposta só destaca; bloqueia só a dúvida que muda a minuta | Confirmado |
