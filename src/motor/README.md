# src/motor/

Núcleo puro do sistema. Recebe o pacote de regras e as respostas e devolve a minuta. Sem banco, sem tela, sem rede, sem data atual e sem aleatoriedade. Uma regra de lint impede importar qualquer coisa de fora daqui.

| Pasta | Responsabilidade | Matrizes |
| --- | --- | --- |
| `pacote/` | tipos e leitura do pacote compilado | todas |
| `wizard/` | próxima pergunta, dependências, pré-preenchimento pelo checklist | M04, M05, M11 |
| `itens/` | regras de cada item: ME/EPP pelo valor, grupo, amostra, marca, validade | M03, M05, M11 |
| `montagem/` | escolha de blocos, preenchimento de lacunas, numeração | M02, M04, M08 |
| `validacao/` | regras determinísticas antes do PDF | M10 |
| `derivacao/` | campos do ETP para blocos do TR (v1) | M06 |
