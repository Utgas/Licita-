# Arquitetura do Licita+

> Cópia de trabalho do documento "Arquitetura do Licita+" (claude.ai), de 22/10/2026. Os diagramas do original estão descritos em texto. Quando um dos dois mudar, atualize o outro.

O Licita+ é um motor de regras. As matrizes viram um pacote de dados versionado, e o código só executa esse pacote: nenhum texto jurídico fica escrito no código. A primeira versão monta o TR sem IA.

## Princípios

Seis regras valem para todas as decisões abaixo. Quando uma escolha técnica contrariar uma delas, a escolha muda.

1. **Regra jurídica é dado, não código.** Texto do modelo AGU, condições e perguntas do wizard ficam nas matrizes. O código lê o pacote compilado e nunca tem cláusula escrita dentro dele.
2. **O motor é isolado e testado antes das telas.** Wizard, montagem e validação são funções puras, sem banco, tela ou rede. Os cenários do agente das matrizes viram testes automáticos.
3. **A primeira versão não usa IA.** Montar o TR por regras não envia nada a terceiros, então não depende da aprovação de um provedor de IA.
4. **Vercel e Supabase, sem prender o motor a eles.** O motor não sabe onde roda, e o banco é PostgreSQL comum. Se a TI exigir outra hospedagem, muda a implantação, não o código.
5. **Cada processo fica preso à versão das regras com que foi criado.** Quando a AGU publicar um modelo novo, entra um pacote novo; os processos antigos continuam reproduzíveis.
6. **Simples na medida da escala.** A unidade faz cerca de 140 pregões por ano, uns 3 por semana. Uma aplicação e um banco bastam. Fila, microsserviço e cache ficam de fora.

## Visão geral

O motor fica no meio do sistema. De um lado ele recebe o pacote compilado das matrizes, e do outro responde às telas.

```text
Matrizes (CSV) ──> Compilador ──> Pacote de regras (JSON versionado, com hash)
                                                │
                                                v
         Motor: wizard · itens · montagem · validação · derivação (v1)
           ^                                              │
           │                                              v
  Aplicação (Vercel) <──> Supabase (PostgreSQL)     Exportação (PDF e texto por campo)
  checklist, wizard,      rascunho, itens,                │ após revisão humana
  revisão                 auditoria                       v
           ^                                        Compras.gov.br (colado à mão)
           ┊ texto com trecho de origem
        IA (v2, só com provedor aprovado)
```

A IA aparece tracejada porque só entra na v2. Até lá, nenhum dado do processo sai do servidor.

## Entrada: o checklist técnico

A entrada principal do sistema é o checklist técnico, e não o DFD. A área requisitante responde aos fatos técnicos, e a equipe administrativa decide o enquadramento jurídico no wizard. É a mesma divisão que o próprio checklist estabelece.

1. A área requisitante preenche o checklist de consumo ou o de permanentes, com a mesma numeração de perguntas do documento atual.
2. Os itens entram por planilha ou pela tabela do DFD, e cada resposta "por item" fica ligada aos itens que ela indica.
3. A equipe administrativa responde ao wizard. O que o checklist já respondeu chega preenchido, e as decisões jurídicas ficam com ela.
4. O motor monta o ETP e o TR, e cada trecho mostra a pergunta do checklist de onde veio.

**Word e digitação pelo operador.** A área requisitante preenche o checklist em Word e o operador o envia ao sistema, que lê as respostas. O operador também pode digitar ou corrigir respostas na tela. Só o operador usa o sistema (decisão 0010).

**A IA perde peso.** Com respostas estruturadas, a v1 já monta o ETP a partir do checklist. Na v2, a IA só melhora a redação, sempre citando a pergunta de origem.

**O checklist está congelado na versão já distribuída às OMs** (decisão 0009). Ele chega por upload do Word preenchido. A leitura destaca em amarelo o que ficou incerto, pergunta ao operador o que muda a minuta e oferece campos de complemento para o que o checklist não pede. Uma versão nova do checklist exige um M11 novo e gera um pacote de regras novo.

## Componentes

São onze componentes, entregues em três versões. A v0 monta o TR por regras. A v1 acrescenta o ETP montado a partir do checklist e a derivação do ETP para o TR. A v2 acrescenta a IA.

| Componente | O que faz | Matrizes que usa | Versão |
| --- | --- | --- | --- |
| Checklist técnico | Leitura do Word preenchido pela área requisitante, enviado pelo operador, com revisão e complementos (decisão 0009) | M11 | v0 |
| Compilador de regras | Lê os CSV, confere IDs e condições e gera o pacote em JSON, com hash | M02 a M07, M10, M11 | v0 |
| Motor: wizard | Escolhe a próxima pergunta pelas dependências e já preenche o que o checklist respondeu | M04, M05, M11 | v0 |
| Motor: itens | Aplica as regras de cada item: ME/EPP pelo valor estimado, grupo, amostra, marca e validade | M03, M05, M11 | v0 |
| Motor: montagem | Escolhe os blocos do TR, preenche as lacunas e refaz a numeração | M02, M04 | v0 |
| Motor: validação | Roda as regras determinísticas antes de liberar o PDF | M10 | v0 |
| Motor: derivação | Leva os campos do ETP para os blocos do TR | M06 | v1 |
| Aplicação | Telas, login, perfis, rascunho e revisão | nenhuma | v0 |
| Exportação | Gera o PDF para leitura e o texto por campo para colar no TR Digital e no ETP Digital | M01, M02 | v0 |
| Auditoria | Registro só de inserção: quem, quando, versão do pacote e hash do PDF | nenhuma | v0 |
| IA | Melhora a redação das seções do ETP a partir do checklist e do DFD, citando a pergunta de origem | M01, M07, M11 | v2 |

As regras setoriais de saúde (M08), como ANVISA, validade e OPME, entram no pacote como blocos condicionais adicionais.

## Pacote de regras

As matrizes são a fonte, e o sistema só executa o pacote compilado a partir delas. Ninguém edita o pacote à mão.

1. Os CSV ficam no repositório, em `matrizes/v1/`, com histórico de cada alteração.
2. O compilador gera `regras/agu-tr-compras-2025-12/pacote.json` e o hash dele.
3. A compilação falha se um ID citado não existir, se uma condição não puder ser lida pela máquina ou se um cenário de teste mudar de resultado sem aviso.
4. O administrador publica o pacote, e cada processo novo grava qual pacote usou.

**As condições estão em formato de máquina.** Desde a Fase 9 das matrizes, M02, M04, M08 e M10 têm colunas `_expr` em JSON Logic, um formato de condições que o sistema avalia sem executar código. O texto livre continua como comentário, e as condições que não couberam estão na P27 das matrizes.

```json
{"bloco": "TR-4.32", "entra_se": {"==": [{"var": "WZ_23"}, "SIM"]}}
```

**Validação humana trava a produção.** O pacote de piloto só é publicado quando todas as regras do tipo CONDICAO da M03 e todas as perguntas da M04 estiverem com `validacao = OK`. Em desenvolvimento, regra sem validação gera só um aviso.

**Modelo novo da AGU vira pacote novo.** O nome do pacote leva a versão do modelo, por exemplo `agu-tr-compras-2026-06`. Os processos antigos continuam no pacote em que nasceram.

## Modelo de dados

O banco não guarda a minuta pronta. Guarda as respostas, os itens e as edições do usuário, e o documento é remontado a partir disso e do pacote de regras. Assim a mesma entrada sempre gera a mesma minuta.

| Entidade | Campos principais | Observação |
| --- | --- | --- |
| OM | UASG, nome, linhas do cabeçalho, endereços de entrega, foro | O administrador cadastra; vira padrão no wizard |
| Usuário | nome, e-mail, OM, perfil | Perfis: operador (quem elabora TR e ETP) e administrador, que só cria usuários (decisão 0010) |
| Processo | NUP, objeto resumido, OM, pacote e hash, situação | Situações: rascunho, em revisão, liberado, concluído |
| Resposta do checklist | processo, versão do checklist, pergunta (CK), valor, itens atingidos | Vem do formulário ou da leitura do Word |
| Resposta do wizard | processo, pergunta (WZ), valor, origem (checklist ou equipe) | Uma linha por pergunta respondida |
| Item | número, especificação, CATMAT, unidade, quantidade, valor unitário de referência, grupo, tratamento ME/EPP, amostra, marca, perecível, validade mínima | O tratamento ME/EPP é calculado pelo valor; só a exceção justificada é escolha |
| Quantidade por órgão | item, UASG, mínima, máxima | Só em registro de preços com participantes |
| Seção editada | processo, documento, bloco ou campo, texto, origem | Só o que o usuário escreveu ou mudou; o resto vem do pacote |
| Evento de auditoria | data e hora, usuário, processo, ação, pacote, hash do PDF | Só inserção; ninguém altera nem apaga |
| Pacote publicado | identificador, versão do modelo AGU, versão do checklist, hash, data, quem publicou | Pacote antigo nunca é apagado |

Os itens entram por importação de planilha. Num registro de preços com dezenas de itens, digitar um por um não é viável. Os valores vêm da pesquisa de preços e nunca são calculados pelo sistema.

## Segurança e retenção

O escopo inicial dizia para não guardar conteúdo, mas, para outra pessoa revisar, o rascunho tem que ficar guardado enquanto o processo está aberto. A regra é guardar durante o trabalho e apagar depois.

| Ponto | Regra |
| --- | --- |
| Rascunho | Respostas, itens e seções editadas ficam guardados enquanto o processo está aberto |
| Expurgo | 30 dias depois de "concluído", o conteúdo é apagado; ficam a auditoria e o hash (prazo configurável) |
| PDF | Gerado na hora, entregue e descartado; nunca gravado |
| DFD (v2) | Lido em memória, anonimizado antes de qualquer envio à IA e descartado |
| Cópias de segurança | As diárias do Supabase Pro ficam 7 dias, dentro do prazo do expurgo; o plano gratuito não tem cópia automática |
| Banco exposto | RLS ligado em toda tabela. Sem RLS, qualquer pessoa com a chave pública, que vai no código da página, lê a tabela. O navegador não consulta o banco; só o servidor |
| Orçamento sigiloso | Quando a resposta da WZ-40 for SIM, os valores saem do PDF de circulação e vão para um anexo de acesso restrito |
| Acesso | Login individual por e-mail e senha (decisão 0010); cada usuário vê só os processos da própria OM. O segundo fator é reavaliado antes do piloto |
| Tráfego | HTTPS obrigatório; banco com criptografia em repouso |
| Registros técnicos | Sem conteúdo de requisição; sem serviço externo de monitoramento que receba dados |
| Recursos externos | Páginas sem fonte, script ou imagem de terceiros; tudo servido pelo próprio sistema |

Documento com informação classificada continua fora do sistema. ETP e TR em elaboração são documentos preparatórios, e por isso o acesso fica restrito à equipe até a publicação.

## Stack

O critério é usar uma linguagem só, ferramentas comuns e nada que prenda o motor a uma nuvem. Ferramenta comum também é a que o agente de código conhece melhor.

| Camada | Escolha | Por quê |
| --- | --- | --- |
| Linguagem | TypeScript em tudo | Motor, telas e scripts no mesmo idioma; os tipos pegam ID e campo errados antes de rodar |
| Aplicação | Next.js na Vercel | Telas e servidor no mesmo projeto, na hospedagem que o Gabriel já domina |
| Banco | Supabase (PostgreSQL) | PostgreSQL comum por baixo; as migrações ficam no repositório |
| Região | Funções da Vercel em São Paulo (gru1); banco do Supabase em São Paulo (sa-east-1) | O padrão da Vercel é Washington (iad1); no mesmo lugar, o dado fica no Brasil e as consultas não atravessam o continente |
| Acesso ao banco | Drizzle ORM, pelo pooler do Supabase | Esquema em TypeScript; o pooler aguenta as conexões curtas das funções |
| Login | Supabase Auth, e-mail e senha | Já vem com o Supabase; o segundo fator pode ser ligado depois sem refazer o login |
| Validação | Zod | Confere o pacote de regras e toda entrada de tela |
| Condições | JSON Logic | Avalia a condição sem executar código |
| PDF | @react-pdf/renderer, no servidor | Roda dentro da função, sem navegador; o Chromium esbarra no limite de 250 MB das funções da Vercel |
| Planilhas | ExcelJS | Importação da tabela de itens |
| Testes | Vitest no motor, Playwright nas telas | Os cenários do agente viram testes de ouro |
| Ambientes | Dois projetos na Vercel e no Supabase: desenvolvimento e produção | Sem Docker na máquina; o desenvolvimento só usa dados fictícios |

Os planos gratuitos da Vercel e do Supabase servem para desenvolver com dados fictícios; uso de trabalho exige plano pago (ver as decisões em aberto). As versões exatas ficam fixadas no projeto.

## Árvore do repositório

Um repositório só, com o motor separado do resto. A pasta `src/motor` não pode importar nada de `dados`, `app`, `auth` ou `ia`, e uma regra de lint quebra o build se isso acontecer.

```text
licita-plus/
├── CLAUDE.md                     # regras para o agente de código
├── README.md                     # como começar e como validar as matrizes
├── supabase/                     # configuração e migrações do banco
├── docs/
│   ├── escopo.md
│   ├── arquitetura.md            # este documento
│   ├── decisoes/                 # uma decisão por arquivo
│   └── tarefas/                  # uma tarefa por marco para o agente de código
├── matrizes/
│   └── v1/                       # CSV das matrizes: fonte da verdade jurídica
├── regras/
│   └── agu-tr-compras-2025-12/   # gerado pelo compilador; não editar à mão
│       ├── pacote.json
│       └── pacote.sha256
├── referencias/                  # modelo AGU e checklists em branco
├── scripts/
│   ├── compilar-regras.ts        # CSV para pacote.json, com todas as checagens
│   └── simular-wizard.ts         # roda os cenários e lista os blocos escolhidos
├── src/
│   ├── motor/                    # núcleo puro: sem banco, sem tela, sem rede
│   │   ├── pacote/               # tipos e leitura do pacote
│   │   ├── wizard/               # próxima pergunta, dependências, respostas
│   │   ├── itens/                # ME/EPP, grupo, amostra, marca, validade
│   │   ├── montagem/             # escolha de blocos, lacunas, numeração
│   │   ├── validacao/            # regras determinísticas (M10)
│   │   └── derivacao/            # ETP para TR (v1)
│   ├── dados/                    # esquema do banco, migrações e consultas
│   ├── auth/                     # login, perfis e permissões
│   ├── auditoria/                # registro só de inserção
│   ├── exportacao/               # HTML do documento, PDF e texto por campo
│   ├── ia/                       # v2: vazio até o provedor ser aprovado
│   └── app/                      # telas e rotas
│       ├── login/
│       ├── processos/            # lista e novo processo
│       │   └── [id]/
│       │       ├── wizard/
│       │       ├── itens/        # importação e atributos de cada item
│       │       ├── revisao/      # minuta montada, edição por bloco, alertas
│       │       └── exportar/     # PDF e botões de copiar por campo
│       └── admin/                # usuários, OMs, pacotes, auditoria
└── testes/
    ├── motor/                    # testes unitários
    ├── cenarios/                 # C1 a C8 e os dois TRs reais de DEZ/2025
    └── telas/                    # fluxo completo no navegador
```

## Plano de construção

São seis marcos, e cada um só termina quando cumpre o critério de saída. Os Marcos 0 a 3 não precisam de autorização, porque usam só dados fictícios e documentos publicados.

| Marco | Versão | Entrega | Sai quando | Depende de |
| --- | --- | --- | --- | --- |
| 0. Esqueleto | v0 | Repositório, CLAUDE.md, testes e compilador lendo as matrizes | O compilador gera o pacote sem erro a partir dos CSV atuais | Nada |
| 1. Motor do TR, sem telas | v0 | Wizard, regras por item, montagem com numeração e validação determinística | C1 a C8 passam e os TRs 23/2026 e 58/2026 são reproduzidos, exceto nos trechos variáveis | Matrizes da Fase 10 (feitas) |
| 2. Telas e banco | v0 | Login, envio e revisão do checklist, itens, wizard, revisão, PDF, copiar por seção do modelo AGU e auditoria | Alguém de fora do desenvolvimento faz um TR do início ao PDF, com dados fictícios | Nada (checklist, formato e expurgo decididos) |
| 3. ETP e derivação | v1 | ETP montado a partir do checklist (M11) e derivação do ETP para o TR (M06) | O par 117/2025 é reproduzido a partir das mesmas respostas | Fases 4 a 9 das matrizes (feitas) |
| 4. Piloto na OM | piloto | 3 processos reais feitos em paralelo com o método atual | Nenhuma ressalva da CJU atribuível ao sistema e tempo de elaboração medido | Regras do M03 e do M04 validadas, hospedagem aprovada, conta e patrocinador formal |
| 5. IA | v2 | IA melhora a redação do ETP a partir do checklist e do DFD, citando a pergunta de origem | Nenhuma citação fora da base curada no banco de testes de DFDs | Provedor de IA aprovado |

O Marco 1 concentra o risco: se o motor não reproduzir os TRs reais, nenhuma tela resolve.

## Decisões em aberto

A versão do checklist, o formato e o prazo de expurgo já foram decididos, e nada mais trava o Marco 2. A validação das regras do M03 e do M04, a aprovação da hospedagem, a conta e o patrocinador travam o Marco 4; o provedor de IA, o Marco 5. Recomenda-se validar as regras aos poucos, durante os Marcos 1 a 3, para o retrabalho não chegar todo junto antes do piloto.

| Decisão | Opções | Recomendação | Trava |
| --- | --- | --- | --- |
| Validação das regras | Validar tudo ou só o que decide o TR | Validar primeiro as regras CONDICAO do M03 e as perguntas do M04, aos poucos, durante os Marcos 1 a 3 | Marco 4 |
| Versão do checklist | Congelar agora ou depois da revisão | Decidido (23/10/2026): a versão já distribuída, sem mudança; o sistema contorna (decisão 0009) | Marco 2 |
| Formato do checklist | Só formulário, só Word ou os dois | Decidido (23/10/2026): os dois. Formulário para quem tem acesso, Word para participantes e outras OMs | Marco 2 |
| Prazo de expurgo | 30, 90 ou 180 dias após "concluído" | Decidido (23/10/2026): 30 dias | Marco 2 |
| Aprovação da hospedagem | Vercel e Supabase, ambos em São Paulo (decidido) | Levar à TI e à chefia antes de qualquer dado real | Marco 4 |
| Conta e plano | Conta pessoal ou conta autorizada pela OM | Gratuito só para desenvolver com dados fictícios. No piloto, plano Pro em conta autorizada pela OM | Marco 4 |
| Patrocinador formal | Chefe da OM ou da seção | Pedir com o Marco 2 pronto, mostrando o sistema funcionando com dados fictícios | Marco 4 |
| Provedor de IA | API paga sem uso dos dados para treino ou modelo hospedado no Exército | Decidir só depois do piloto, com o ganho medido | Marco 5 |
| Uso interno ou produto | Só a OM, várias OMs ou venda | Só a OM até o fim do piloto; o modelo de dados já aceita várias OMs | Nada por enquanto |

## Regras para o agente de código

Estão no `CLAUDE.md` da raiz.
