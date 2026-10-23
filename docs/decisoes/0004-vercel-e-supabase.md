# 0004. Hospedagem na Vercel e banco no Supabase

- Data: 22/10/2026
- Situação: aceita

## Contexto

O Gabriel já domina Vercel e Supabase. A escala é pequena: cerca de 140 pregões por ano.

## Decisão

- Aplicação Next.js na Vercel, com funções na região de São Paulo (`gru1`).
- Banco e login no Supabase, região de São Paulo (`sa-east-1`).
- Dois projetos em cada um: desenvolvimento, só com dados fictícios, e produção.
- PDF gerado no servidor com `@react-pdf/renderer`, porque o Chromium não cabe no limite das funções da Vercel.

## Consequências

- Toda tabela com RLS ligado. Sem RLS, qualquer pessoa com a chave pública lê a tabela.
- Os planos gratuitos servem só para desenvolver. O Hobby da Vercel é para uso pessoal não comercial, e o Free do Supabase pausa e não tem cópia automática. O piloto exige plano Pro, numa conta autorizada pela OM.
- O motor não depende de nenhum recurso exclusivo da Vercel ou do Supabase. Se a TI exigir outra hospedagem, muda a implantação, não o motor.
