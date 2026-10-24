# testes/

- `motor/`: testes unitários do motor.
- `cenarios/`: cenários de ouro (C1 a C8 da simulação do agente das matrizes) e a reprodução dos TRs reais feitos sobre o modelo DEZ/2025. Os dados dos cenários são fictícios.
- `telas/`: fluxo completo no navegador (Marco 2, passo 14), com Playwright: login, novo processo, Word fictício montado a partir do checklist em branco, travas, itens, wizard, minuta, cópia das seções, PDF e conclusão; e o operador de outra OM sem acesso. `npm run test:telas`, depois de `testes/telas/preparar.ts`.
- `dados/`: RLS, auditoria e expurgo no Supabase local (`npm run test:banco`, decisão 0013).
- `compilador/`: testes do compilador de regras, com matrizes fictícias em `fixtures/` (decisão 0006).
