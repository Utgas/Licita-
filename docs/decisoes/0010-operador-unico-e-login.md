# 0010. Um perfil de uso, login por e-mail e senha e exportação pelo modelo AGU

- Data: 24/10/2026
- Situação: aceita. Decisão do dono do projeto.

## Contexto

A arquitetura previa quatro perfis (requisitante, elaborador, revisor e administrador) e login com segundo fator. Ao desenhar as telas do Marco 2, o dono do projeto definiu quem usa o sistema, como entra e como a minuta sai.

## Decisão

1. **Só o operador usa o sistema**: quem elabora TR e ETP na equipe de licitação. A área requisitante não entra; ela preenche o checklist em Word, e o operador envia o arquivo (decisão 0009). O administrador só cria usuários.
2. **Login por e-mail e senha**, com redefinição de senha e sem cadastro aberto.
3. **Exportação sempre pelas seções do modelo de TR da AGU**, na ordem e com os títulos do modelo. Ajuste feito no Compras.gov.br fica fora do sistema.

## Consequências

- Somem as telas e as permissões de requisitante e revisor. A revisão é feita pelo próprio operador, na tela da minuta.
- **Risco aceito para o desenvolvimento, a reavaliar antes do piloto:** sem segundo fator, uma senha vazada dá acesso aos processos. O Supabase Auth permite ligar o segundo fator depois, sem refazer o login. A decisão final fica para a aprovação da hospedagem com a TI da OM (Marco 4).
- O brasão da OM entra no cabeçalho só depois de autorizado; o arquivo não vai para o repositório enquanto ele for público.
