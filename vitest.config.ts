import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["testes/**/*.test.ts"],
    // Testes de banco precisam do Supabase local: npm run test:banco.
    exclude: ["testes/dados/**", "node_modules/**"],
    environment: "node",
  },
});
