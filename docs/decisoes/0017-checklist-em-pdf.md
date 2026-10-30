# 0017. Checklist também em PDF e em .odt, com leitura mais tolerante

- Data: 30/10/2026
- Situação: aceita. Pedido do Gabriel: os checklists do HCE chegam em PDF, e o sistema só lia `.docx`.

## Contexto

As OMs preenchem o checklist distribuído no Word, mas muitas mandam o PDF (salvo pelo Word ou pelo LibreOffice, às vezes assinado digitalmente). Os três PDFs que o HCE mandou em 30/10/2026 têm exatamente as perguntas da versão distribuída de permanentes: o problema era só o formato. Eles também mostraram jeitos de marcar que a leitura não conhecia: o X colado na caixa ("☐X", "X☐", "☐ XNão") e o valor escrito embaixo do rótulo ou colado nele ("NomeFulano").

Os PDFs do HCE têm dados reais e não entram no repositório. Os testes usam PDFs fictícios gerados do Word fictício.

## Decisão

1. **Biblioteca:** `pdfjs-dist` (Mozilla), versão fixada. Só extrai o texto e a posição de cada trecho, no servidor, sem rede e sem executar nada do arquivo (a versão 6 nem tem mais o modo que avaliava código das fontes). Ela traz `@napi-rs/canvas` como dependência opcional, que a leitura de texto não usa.
2. **Mesma leitura:** o PDF vira os mesmos blocos do Word (`src/dados/leitura-checklist/pdf.ts`) e segue a mesma leitura (`ler.ts`). Versão reconhecida pelos enunciados, como no Word: PDF de outra versão é erro, nunca leitura parcial.
3. **Montagem do texto pela posição:** linhas pela altura na página; cabeçalho e rodapé repetidos saem; o que vem depois de "Resposta:" é a caixa; o valor embaixo do rótulo vai para a mesma célula (só no cabeçalho e em linhas com duas células ou mais, como a 1.4).
4. **Marcas novas** (valem para o Word e para o PDF): X colado antes ou depois do ☐, maiúsculo ou minúsculo. Campo da 1.4 com o valor colado no rótulo.
5. **Fora do alcance:** PDF escaneado (só imagem) não tem texto; é erro claro, sem OCR. Word antigo (`.doc`) também é erro claro, pedindo para salvar como `.docx` ou PDF.
6. **Origem gravada:** continua `LEITURA_WORD` para os dois formatos (sem migração); a tela mostra "lida do arquivo".

## Revisão de 30/10/2026 (estudo da leitura)

O Gabriel relatou que nem o Word do HCE era lido. O estudo da leitura simulou o que o Word e quem preenche fazem com o arquivo e achou estas falhas, todas corrigidas e com teste em `testes/dados/leitura.test.ts`:

| Situação | Antes | Agora |
| --- | --- | --- |
| Qualquer parágrafo a mais com cara de pergunta ("4.5. ver anexo") | arquivo inteiro recusado como "versão desconhecida" | vira resposta escrita fora da caixa |
| Pergunta com numeração automática do Word ou do LibreOffice (o número sai do texto) | arquivo recusado | pergunta reconhecida pelo enunciado |
| Resposta escrita na mesma linha de "Resposta:" ou num parágrafo fora da caixa | resposta perdida sem aviso | lida como resposta |
| Caixa de seleção de formulário antigo do Word (FORMCHECKBOX) | marca ignorada | lida |
| Texto dentro de marcação `customXml`, linha ou célula dentro de controle de conteúdo, tabela dentro da caixa | texto perdido | lido |
| Mesmo item citado duas vezes numa resposta por item | duas linhas iguais e erro genérico do banco ("Não foi possível salvar") | os textos são juntados |
| Arquivo salvo no formato do LibreOffice (.odt), que é o que o HCE usa | "não é um documento do Word" | lido (`src/dados/leitura-checklist/odt.ts`, mesmas bibliotecas do Word) |
| Pergunta que falta ou mudou | "primeira diferença na pergunta X", às vezes apontando a pergunta errada | diz qual pergunta falta e o texto esperado |

A versão continua reconhecida pelos enunciados do M11: todas as perguntas da versão distribuída, na ordem, com o mesmo texto (sem contar maiúsculas, acentos, aspas e espaços). O que é do modelo (orientação e opções, pelas colunas `orientacao` e `opcoes` do M11) não vira resposta.

**Tela de anexo.** Um espaço para cada checklist (material permanente e material de consumo). "Anexar" abre a escolha do arquivo; escolhido, o botão vira "Ler". O arquivo do outro checklist anexado no espaço errado é recusado com mensagem clara. Se o processo foi criado sem um dos checklists, o espaço dele oferece "Usar também o checklist de ...", que inclui o checklist no processo (registrado na auditoria como alteração do processo). Arquivo maior que 4 MB é avisado antes do envio.

## Consequências

- Uma versão nova do pdfjs-dist só entra com teste (`testes/dados/leitura-pdf.test.ts`).
- Os PDFs fictícios ficam em `testes/dados/fixtures/` (exceção no `.gitignore`) e são gerados por `testes/dados/gerar-pdfs-ficticios.ts`, que exige LibreOffice. O teste não exige.
- Resposta escrita em texto onde deveria haver marca ("Sim" na caixa, sem marcar o ☐) continua sem resposta e destacada para o operador: decidir que o texto vale como marca é regra de leitura do M11, não do código.
