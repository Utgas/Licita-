# 0007. Repositório ctresb/leis como fonte auxiliar

- Data: 23/10/2026
- Situação: aceita

## Contexto

O repositório público ctresb/leis (GitHub) traz leis e decretos federais em Markdown, com um cabeçalho que informa a versão do texto e se a norma foi revogada. Ele ajuda a localizar dispositivos citados no M07. Na conferência feita na Fase 10, apareceram limites:

- o arquivo da Lei 14.133/2021 traz só as partes vetadas e promulgadas depois, não a lei inteira;
- muitos decretos estão só na versão original, sem as alterações posteriores;
- as INs SEGES 58/2022, 65/2021, 73/2022 e 81/2022 não estão lá.

## Decisão

- O ctresb/leis é fonte auxiliar, nunca fonte de verdade. Serve para localizar o dispositivo; a situação e o texto vigente são conferidos no Planalto ou no gov.br.
- Só vale arquivo com `versao_texto` igual a "compilada (texto vigente)", ou "dados abertos do tribunal" para súmulas do TCU. Arquivo "original" não é usado.
- O arquivo da Lei 14.133 do repositório não é usado.
- Nada do repositório é copiado para este projeto. O M07 registra o commit consultado e o caminho de cada arquivo (`matrizes/v1/log_fase10_repo_leis.md`).
- O sistema não consulta o repositório em tempo de execução. Uma consulta assim seria serviço externo e exigiria outra decisão (regra 6 do `CLAUDE.md`).

## Consequências

- Atualizar uma norma no M07 continua sendo trabalho do agente das matrizes, com conferência na fonte oficial.
- Se o repositório mudar ou sumir, nada no Licita+ quebra.
