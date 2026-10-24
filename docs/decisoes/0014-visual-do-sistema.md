# 0014. Visual do sistema: ferramenta de trabalho com cara de documento

- Data: 24/10/2026
- Situação: aceita. Pedido do dono do projeto: o sistema não pode ter "cara de IA" e o front pode mudar agora.

## Contexto

O passo 13 do Marco 2 deixava o visual para a última camada, e não há desenho em `docs/design/`. O dono do projeto
pediu que o sistema não tenha cara de IA: nada de degradê roxo, fonte serifada, fundo quadriculado, três cards de
benefícios, emoji no meio do texto, brilho, layout de sempre e ícone genérico demais. Pediu também que fossem
avaliadas bibliotecas de design e de animação: Unlumen UI, GetLayers, MotionSites, 21st.dev, three.js, GSAP e
anime.js.

Quem usa o Licita+ é o operador da equipe de licitação, que passa horas lendo minuta, conferindo resposta e colando
texto no Compras.gov.br, em computador de OM. O que importa é ler bem, achar a pendência rápido e confiar no que está
na tela.

## O que foi avaliado

| Biblioteca | O que é | Decisão |
| --- | --- | --- |
| Unlumen UI | Componentes React (Tailwind e Motion) instalados pelo registro do shadcn; exemplos: botão com brilho, fundo líquido, imagem que aparece na rolagem | Fora: é estética de página de vitrine, justamente a "cara de IA" que se quer evitar |
| 21st.dev | Catálogo comunitário de componentes no padrão shadcn, copiados para o projeto | Fora: o modelo (código copiado, sem dependência) é bom, mas o acervo é de landing page; nada ali resolve tela de formulário e documento |
| GetLayers | Banco de seções de site (hero, blocos, cenas 3D, vídeo de fundo) para usar com ferramentas de IA | Fora: é para site de marketing |
| MotionSites | Biblioteca paga de prompts e fundos animados para gerar sites com IA | Fora: produz exatamente o visual que se quer evitar |
| three.js | 3D no navegador (WebGL) | Fora: não há nada em 3D no sistema; pesa, gasta bateria e atrapalha leitor de tela |
| GSAP | Animação em JavaScript; gratuita desde 2025, inclusive para uso comercial | Fora: sem necessidade; o pouco movimento do sistema é transição de cor e borda em CSS |
| anime.js | Animação leve em JavaScript | Fora: mesmo motivo do GSAP |

Referências que serviram de fato: os sistemas de design de governo (GOV.UK Design System, U.S. Web Design System e o
Padrão Digital de Governo do gov.br), que priorizam leitura, contraste e foco visível.

## Decisão

1. **Nenhuma biblioteca nova de interface ou animação.** O visual é feito com o que já está na stack: Tailwind e
   `next/font`.
2. **Fontes:** IBM Plex Sans (texto e minuta) e IBM Plex Mono (códigos como WZ-03 e VAR-034, números de processo e
   hashes), sem serifa. Baixadas no build pelo `next/font` e servidas pelo próprio sistema; nenhuma página busca fonte
   de terceiros (arquitetura, "Recursos externos").
3. **Cores** (tokens em `src/app/globals.css`):
   - papel claro e tinta escura;
   - botão principal em tinta;
   - verde-oliva só para marcar a etapa atual;
   - estados do passo 13: vermelho para trava, amarelo para destaque e lacuna, azul para valor padrão, verde para ok.

   Todo texto tem contraste de 6,7:1 ou mais. Nada de degradê, brilho ou sombra.
4. **Ícones próprios** (`src/app/componentes/icones.tsx`): um conjunto pequeno, desenhado para o que o sistema faz.
   - Exemplos: cadeado para trava, losango de sinalização para atenção, colchetes para lacuna, etiqueta para valor
     padrão, balança para decisão jurídica.
   - Todos no mesmo traço; ícone sempre junto de texto.
   - Os emojis saíram de todas as telas.
5. **Componentes comuns** (`src/app/componentes/ui.tsx`):
   - selo de estado;
   - aviso com barra lateral;
   - título de seção;
   - classes de botão e de campo.
6. **Telas:**
   - barra institucional escura e fina;
   - trilho das cinco etapas com a posição atual e as pendências de cada uma;
   - minuta mostrada como folha de documento, com o estado da minuta numa coluna ao lado;
   - login com o sumário do que o sistema faz.
7. **Acessibilidade:**
   - foco com contorno de tinta e halo amarelo, contorno claro na barra escura;
   - alvos de 44 px;
   - nenhum movimento para quem pede menos movimento (`prefers-reduced-motion`);
   - sem rolagem lateral em tela de celular.

## Consequências

- O visual não depende de biblioteca de terceiros: mudar a cor ou a fonte é mexer nos tokens de `globals.css` e no
  `layout.tsx`.
- Componente com comportamento mais complexo (diálogo, menu), se um dia for preciso, entra como código próprio ou
  com uma biblioteca de componentes acessíveis sem estilo, com nova decisão.
- Os testes de tela procuram texto, não símbolo: "Copiado", "Trava", "Sem travas".
