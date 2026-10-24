# 0012. Administrador da TI cuida dos acessos e das senhas; sem redefinição por e-mail

- Data: 24/10/2026
- Situação: aceita. Decisão do dono do projeto. Altera em parte a decisão 0010.

## Contexto

A decisão 0010 previa "esqueci minha senha" com redefinição por e-mail e um administrador que só cria usuários. Ao configurar os ambientes do Marco 2, o dono do projeto definiu que a troca de senha passa pela TI. No plano gratuito, o e-mail padrão do Supabase só chega aos membros da equipe do projeto, o que também inviabilizava a redefinição por e-mail para os usuários.

## Decisão

1. **Só a OM do dono do projeto usa o sistema.** As outras OMs só preenchem o checklist em Word (decisão 0009); elaborar TR e ETP é tarefa exclusiva desta OM. O banco continua com a tabela `om` e o isolamento por OM no RLS, para o sistema poder crescer sem refazer o esquema.
2. **Dois perfis:** `OPERADOR` (elabora TR e ETP) e `ADMINISTRADOR` (a TI, o "superadministrador").
3. **O administrador da TI:**
   - cria e desativa usuários;
   - troca senha de quem esqueceu, sempre com **senha provisória**: o usuário é obrigado a criar a própria senha no primeiro acesso, para a TI não conhecer a senha definitiva e a auditoria continuar provando quem fez o quê;
   - lê a auditoria (quem, quando, o quê e hashes), sem poder alterá-la;
   - **não abre processos**: não vê respostas, itens nem minuta. TR e ETP em elaboração são documentos preparatórios, de acesso restrito à equipe.
4. **"Esqueci minha senha"** não envia e-mail: a tela diz para procurar a TI.
5. **O operador troca a própria senha** depois de entrar, informando a senha atual.
6. O primeiro administrador é criado por script (`npm run criar-usuario`), com a chave secreta do Supabase; os demais, pela tela do administrador.

## Consequências

- Sai do Marco 2 o envio de e-mail e a tela de redefinição por link; entram a tela "Alterar minha senha", a troca obrigatória da senha provisória e a tela do administrador (usuários, senhas e auditoria).
- Toda ação do administrador (criar, desativar, trocar senha) grava linha na auditoria.
- Nenhum serviço de e-mail externo é necessário por enquanto.
- O risco da decisão 0010 (sem segundo fator) continua e é reavaliado antes do piloto.
