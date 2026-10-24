/**
 * Testes de tela (Marco 2, passo 14): o fluxo inteiro no navegador, contra o Supabase local com os usuários de
 * testes/telas/preparar.ts. Só dados fictícios. Uso: npm run test:telas (sobe o sistema se ele não estiver no ar).
 */
import { defineConfig, devices } from "@playwright/test";

const porta = Number(process.env.PORTA_DOS_TESTES ?? 3000);

export default defineConfig({
  testDir: "testes/telas",
  testMatch: "**/*.spec.ts",
  timeout: 5 * 60 * 1000,
  expect: { timeout: 30 * 1000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${porta}`,
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    trace: "retain-on-failure",
    ...devices["Desktop Chrome"],
  },
  webServer: {
    command: process.env.CI ? `npm run start -- -p ${porta}` : `npm run dev -- -p ${porta}`,
    url: `http://localhost:${porta}/login`,
    reuseExistingServer: true,
    timeout: 3 * 60 * 1000,
    // Log do servidor junto do log do teste (erro de login ou de banco aparece no CI).
    stdout: "pipe",
    stderr: "pipe",
  },
});
