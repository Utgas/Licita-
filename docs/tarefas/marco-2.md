# Marco 2: telas e banco

**Objetivo:** o operador entra no sistema, cria um processo, envia o checklist em Word, revisa a leitura, confere os itens, responde ao wizard, revisa a minuta, copia cada seção para o Compras.gov.br e baixa o PDF. Tudo com dados fictícios, no plano gratuito da Vercel e do Supabase.

**Critério de saída:** alguém de fora do desenvolvimento faz um TR do início ao PDF, com dados fictícios, sem ajuda.

**Antes de começar:** leia `CLAUDE.md`, `docs/arquitetura.md` e as decisões 0009 (checklist), 0010 (operador único, login e exportação) e 0011 (dependências e pastas deste marco). Trabalhe no ramo `marco-2`, criado a partir do `main`.

## Regras deste marco

- O motor (`src/motor`) só muda no passo 0. Depois dele, se uma tela precisar de algo que o motor não dá, pare e avise.
- Nenhuma consulta ao banco sai do navegador: tudo passa por código de servidor (Server Actions ou Route Handlers) com Drizzle.
- Toda tabela nasce com RLS ligado e com política testada.
- Segredos (chaves do Supabase, senha do banco) só em variáveis de ambiente. Nunca no repositório, em log ou em mensagem de commit.
- Nada do acervo institucional entra no repositório: nem brasão, nem foto, nem documento. O cabeçalho tem só o espaço do brasão, com um marcador neutro.
- Fontes servidas pelo próprio sistema (`next/font`); nenhum script, fonte ou imagem de terceiros nas páginas.
- Todo texto jurídico continua vindo do pacote de regras. A tela pode ter texto de interface, nunca cláusula, pergunta ou condição.

## Passos

0. **Matrizes da Fase 15** (já no ramo `marco-2`). Hoje o compilador recusa o formato `POR_ITEM_AGRUPADO` no `lacunas_mapa` do M08, e o motor ainda não conhece as novidades. Ajuste o compilador e o motor, seguindo o simulador do agente das matrizes (`matrizes/v1/scripts/`, só leitura), para:
   - a coluna "PARTICIPAÇÃO" na TR-1.1.TAB1 (`tabela_colunas`), com os textos da Fase 15;
   - a concordância de número (singular ou plural pelo número de itens) e o formato `POR_ITEM_AGRUPADO` (itens com o mesmo valor agrupados) nas cláusulas setoriais;
   - os complementos CK-X-10 a CK-X-19, lidos pelo mapa do M08;
   - a DV-42 na reprodução do R2.

   Os cenários de ouro, a reprodução e `npm run simular -- C8` voltam a passar ("O item 1 será transportado…"). Só então siga para o passo 1. É o único passo deste marco que mexe no motor.

1. **Contas e ambientes.** Pare e passe ao Gabriel, em português simples e passo a passo, o que ele precisa fazer:
   - criar o projeto de desenvolvimento no Supabase, na região São Paulo (sa-east-1), no plano gratuito;
   - ligar o repositório a um projeto na Vercel, com funções em São Paulo (gru1, já no `vercel.json`);
   - onde copiar cada chave e onde colar (variáveis de ambiente da Vercel, `.env.local` local e segredos do GitHub Actions, se os testes de banco rodarem lá).

   Acrescente ao `.env.example` só os nomes das variáveis, sem valores. Siga quando o Gabriel confirmar.

2. **Esquema do banco** (`supabase/migrations/` e `src/dados/esquema.ts`), com Drizzle. Tabelas mínimas:
   - `om`;
   - `usuario`: perfil `OPERADOR` ou `ADMINISTRADOR`, ligado ao usuário do Supabase Auth;
   - `processo`: número, objeto, modalidade, registro de preços, checklists usados, etapa, situação, data de conclusão e pacote de regras usado;
   - `resposta_checklist`: pergunta CK, valor, texto livre, número lido, itens atingidos e origem (leitura do Word ou operador);
   - `revisao_confirmada`: pergunta, motivo e resposta do operador;
   - `complemento_operador`: CK-X;
   - `item`: dados de entrada do M05;
   - `resposta_wizard`: valor, justificativa e origem (checklist, sugestão aceita ou equipe);
   - `exportacao`: seção copiada e hash do PDF;
   - `auditoria`: quem, quando, o quê e hashes. Só aceita inclusão.

   Cada usuário só vê os processos da própria OM. RLS em todas, com testes que provam que um usuário de outra OM não lê nem escreve.

3. **Login** (`src/auth/`), com Supabase Auth:
   - e-mail e senha, "esqueci minha senha" e redefinição;
   - sem cadastro aberto: o administrador cria usuários por um script (`npm run criar-usuario`) ou por uma tela simples só para ele;
   - sessão expirada leva ao login sem perder o que já foi salvo;
   - todas as rotas, menos login e redefinição, exigem sessão.

4. **Auditoria** (`src/auditoria/`): toda escrita grava uma linha. Exemplos: leitura do checklist com o hash do arquivo, resposta do wizard, confirmação de revisão, minuta gerada com o hash do pacote, PDF baixado com o hash do PDF e processo concluído.

5. **Painel e novo processo:**
   - lista com etapa, pendências e "Será apagado em DD/MM" nos concluídos, mais busca e filtros;
   - formulário de novo processo: número, objeto, modalidade, registro de preços e checklists.

6. **Leitura do checklist** (`src/dados/leitura-checklist/`). Leitura determinística do Word preenchido, sem IA:
   - abre o `.docx` com `jszip` e lê o XML com `fast-xml-parser` (decisão 0011);
   - identifica cada pergunta pelo número e confere o enunciado com o do M11;
   - lê as marcas de opção (☒, ☑, X no lugar do ☐) e a resposta na caixa abaixo de "Resposta:";
   - produz exatamente os dados que as expressões usam: respostas `CK_*`, `_texto`, `_numero`, `checklist.consumo`, `checklist.permanentes` e `checklist.marcas_multiplas`, como descreve a coluna `leitura` do M11 e o README das matrizes;
   - reconhece a versão do checklist pelo hash dos enunciados; versão desconhecida é erro claro, nunca leitura parcial;
   - o arquivo é descartado depois da leitura; fica só o hash (decisão 0009).

   Testes: monte Words preenchidos fictícios a partir dos checklists em branco de `referencias/`, por código, cobrindo cada motivo de revisão (sem resposta, duas marcas, "Outro" ilegível, nome de pessoa, resposta única para vários itens).

   O operador também pode digitar ou corrigir respostas na tela, sem o Word.

7. **Tela do checklist.** Mostra a leitura com os estados da revisão (`revisao_motivos`):
   - **trava** (vermelho): pergunta ao operador, com botões de resposta;
   - **destaque** (amarelo): só aviso;
   - **ok** (verde).

   Ao lado, os complementos do operador (CK-X). A confirmação vai para `revisao_confirmada`.

8. **Tela dos itens:**
   - entrada manual e importação de planilha (ExcelJS), com colunas fixas e um modelo de planilha para baixar;
   - participação ME/EPP calculada pelo motor, nunca digitada;
   - linhas de cota no fim, sem renumerar;
   - chave de orçamento sigiloso;
   - painel "como o item foi classificado", com os dados que o motor devolve.

9. **Tela do wizard:**
   - lista das perguntas com estado (respondida, veio do checklist, decisão jurídica pendente) e uma pergunta por vez;
   - a sugestão do checklist aparece marcada como sugestão;
   - campos extras e justificativas obrigatórias como o motor pedir.

10. **Tela da minuta:**
    - o texto vem do motor, com lacunas em amarelo e valores padrão em azul;
    - cada trecho é clicável e mostra a origem: bloco, motivo, respostas, nota e norma;
    - faixa de bloqueios no topo e cartão de conferência manual (regras do M10 sem expressão);
    - o operador não edita o texto: corrige respostas e dados, e a minuta é montada de novo.

11. **Exportar** (`src/exportacao/`):
    - uma linha por seção do modelo de TR da AGU, na ordem e com os títulos do modelo (decisão 0010), com botão "Copiar" e marca de copiado;
    - PDF gerado no servidor com `@react-pdf/renderer`, baixado na hora e nunca guardado; o hash vai para a auditoria;
    - exportar só fica liberado sem travas;
    - botão "Marcar como concluído".

12. **Expurgo.** Tarefa diária no banco (`pg_cron`) que apaga os dados de processo 30 dias depois de "concluído". A auditoria fica. Teste com a data simulada: o processo some e a auditoria continua.

13. **Visual.** Se houver um desenho em `docs/design/` (do Super Design), siga-o. Se não houver, use componentes simples com Tailwind e o código de cores dos estados: vermelho trava, amarelo destaca, azul é valor padrão, verde é ok. Sempre com texto ou ícone junto da cor, contraste de 4.5:1 e alvos de 44 px. Não espere o desenho para os passos 2 a 12: o visual é a última camada.

14. **Testes de ponta a ponta** (Playwright). O fluxo inteiro com um processo fictício: login, novo processo, envio do Word fictício, resolução das travas, itens, wizard, minuta sem travas, cópia de todas as seções, PDF e conclusão. Mais um teste de que usuário de outra OM não vê o processo.

15. **Publicar no ambiente de desenvolvimento** da Vercel, e passar ao Gabriel o endereço e um usuário de teste.

## Critério de saída

- O fluxo do passo 14 passa no GitHub Actions e no ambiente publicado.
- `npm test`, `npm run lint`, `npm run typecheck` e os cenários de ouro continuam passando.
- RLS testada em todas as tabelas.
- Alguém de fora do desenvolvimento faz um TR do início ao PDF sem ajuda.

## Não faça

- IA, ETP, dados reais, brasão ou qualquer material do acervo da OM.
- Mudança nas matrizes ou no comportamento do motor.
- Dependência fora da stack e da decisão 0011 sem perguntar.

## Ao terminar cada passo

Diga o que mudou, como o Gabriel testa (de preferência clicando no ambiente publicado) e o que ficou pendente. Um commit por passo.
