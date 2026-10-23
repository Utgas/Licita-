# 0009. O checklist já distribuído não muda: o sistema contorna

- Data: 23/10/2026
- Situação: aceita. Decisão do Gabriel no chat de gestão do projeto (lote 2).

## Contexto

O agente das matrizes propôs 21 ajustes nos checklists de consumo e de permanentes (`matrizes/v1/sugestoes_checklist.md`, S01 a S19, e S20 e S21 propostas pelo gestor). Os dois checklists em Word já foram enviados às OMs e não podem ser alterados. Eles chegam ao sistema por upload do Word preenchido.

## Decisão

1. **Versão congelada.** A versão em uso é a de `referencias/` (hashes no `matrizes/v1/README.md`). O M11 mapeia essa versão e nenhuma outra. O formulário do sistema usa os mesmos IDs.
2. **Ambiguidades e duplicidades (S01 a S09, S20).** O Word não muda, então o sistema trata cada caso na leitura:
   - toda resposta incerta (duas marcas em pergunta de uma opção, duplicidade com respostas diferentes, "Outro" sem número, nome de pessoa onde deveria haver setor, resposta única para vários itens) fica **destacada em amarelo** na tela de revisão da leitura;
   - quando a dúvida muda a minuta, o sistema também **faz a pergunta ao operador**, e a geração fica bloqueada até a resposta (VAL-037);
   - a regra de cada caso (qual resposta prevalece, quando destacar, o que perguntar) fica no M11, nunca no código.
3. **Lacunas (S10 a S18).** Os dados que o checklist não pede viram **campos de complemento** que o operador preenche no sistema, ligados às mesmas variáveis. Não há opção pré-definida que não venha de norma: o prazo de avaliação (S12) é digitado em dias úteis.
4. **S19 (controles de conteúdo do Word).** Fica para uma versão futura do checklist; não se aplica ao Word já distribuído.
5. **S21 (comodato, seção 10 do consumo).** A seção continua no Word. O sistema lê, guarda só para controle e não leva nada à minuta até o estudo do comodato (decisão 0008).
6. **Upload.** O Word enviado é lido e descartado; ficam as respostas extraídas e o hash do arquivo.

## Consequências

- A leitura do Word (Marco 2) passa a ter uma etapa obrigatória de revisão pelo operador.
- O M11 ganha a descrição da leitura e da revisão de cada pergunta, e linhas de complemento do operador.
- Uma versão nova do checklist, no futuro, gera um M11 novo e um pacote novo; as duas versões convivem.
