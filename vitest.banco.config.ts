import { defineConfig } from "vitest/config";

// Testes de banco (RLS, auditoria, expurgo): rodam no Supabase local (npx supabase start), um arquivo por vez.
export default defineConfig({
  test: {
    include: ["testes/dados/**/*.test.ts"],
    environment: "node",
    fileParallelism: false,
    testTimeout: 20000,
  },
});
