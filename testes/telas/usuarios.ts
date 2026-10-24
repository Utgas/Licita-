/** Usuários fictícios dos testes de tela, criados por preparar.ts no Supabase local. Senhas só de teste. */
export const USUARIOS = {
  operador: { email: "operador@om-a.exemplo.invalid", senha: "SenhaDeTeste123", perfil: "OPERADOR", om: "999998" },
  administrador: { email: "admin@om-a.exemplo.invalid", senha: "SenhaDeTeste123", perfil: "ADMINISTRADOR", om: "999998" },
  operadorOutraOm: { email: "operador@om-b.exemplo.invalid", senha: "SenhaDeTeste123", perfil: "OPERADOR", om: "999997" },
} as const;
