/**
 * Proteções e LGPD no navegador (decisão 0017): cabeçalhos de segurança, páginas legais abertas, aviso de cookies,
 * atalho de teclado para o conteúdo, limite de tentativas de login e pedido do titular respondido pela TI. Precisa
 * do Supabase local preparado por testes/telas/preparar.ts. Só dados fictícios.
 */
import { randomInt, randomUUID } from "node:crypto";
import { type Browser, type Page, expect, test } from "@playwright/test";
import { USUARIOS } from "./usuarios.ts";

// IP fictício (faixa de documentação) por contexto: as falhas deste teste não bloqueiam o IP dos outros testes.
const ipFicticio = () => `203.0.113.${randomInt(1, 255)}`;
const novaPagina = async (browser: Browser) => (await browser.newContext({ extraHTTPHeaders: { "x-forwarded-for": ipFicticio() } })).newPage();

async function entrar(page: Page, usuario: { email: string; senha: string }, destino: RegExp) {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(usuario.email);
  await page.getByLabel("Senha", { exact: true }).fill(usuario.senha);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL(destino, { timeout: 30000 });
}

test("cabeçalhos de segurança em toda página", async ({ request }) => {
  const resposta = await request.get("/login");
  const h = resposta.headers();
  expect(h["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(h["content-security-policy"]).toContain("default-src 'self'");
  expect(h["x-frame-options"]).toBe("DENY");
  expect(h["x-content-type-options"]).toBe("nosniff");
  expect(h["referrer-policy"]).toBe("same-origin");
  expect(h["x-powered-by"]).toBeUndefined();
});

test("política de privacidade e termos abrem sem login, e o rodapé leva a eles", async ({ browser }) => {
  const page = await novaPagina(browser);
  await page.goto("/privacidade");
  await expect(page).toHaveURL(/\/privacidade$/);
  await expect(page.getByRole("heading", { level: 1, name: "Política de Privacidade" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "7. Cookies" })).toBeVisible();
  await page.getByRole("navigation", { name: "Informações legais" }).getByRole("link", { name: "Termos de Uso" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Termos de Uso" })).toBeVisible();
});

test("aviso de cookies some com Entendi e não volta", async ({ browser }) => {
  const page = await novaPagina(browser);
  await page.goto("/login");
  const aviso = page.getByRole("region", { name: "Aviso de cookies" });
  await expect(aviso).toBeVisible();
  await aviso.getByRole("button", { name: "Entendi" }).click();
  await expect(aviso).toBeHidden();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
  await expect(aviso).toBeHidden();
});

test("o primeiro Tab mostra o atalho para o conteúdo, e o login funciona só pelo teclado", async ({ browser }) => {
  const page = await novaPagina(browser);
  await page.goto("/login");
  await page.keyboard.press("Tab");
  const atalho = page.getByRole("link", { name: "Pular para o conteúdo" });
  await expect(atalho).toBeFocused();
  await expect(atalho).toBeVisible();
  await page.keyboard.press("Enter");
  await page.getByLabel("E-mail").focus();
  await page.keyboard.type(USUARIOS.operador.email);
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Senha", { exact: true })).toBeFocused();
  await page.keyboard.type(USUARIOS.operador.senha);
  await page.keyboard.press("Enter");
  await page.waitForURL(/\/processos(\/|$)/, { timeout: 30000 });
});

test("5 senhas erradas bloqueiam o e-mail, mesmo com a senha certa depois", async ({ browser }) => {
  const page = await novaPagina(browser);
  const usuario = { email: `inexistente-${randomUUID().slice(0, 8)}@exemplo.invalid`, senha: "SenhaErrada123" };
  await page.goto("/login");
  const tentar = async () => {
    await page.getByLabel("E-mail").fill(usuario.email);
    await page.getByLabel("Senha", { exact: true }).fill(usuario.senha);
    await Promise.all([page.waitForResponse((r) => r.request().method() === "POST"), page.getByRole("button", { name: "Entrar" }).click()]);
    await expect(page.getByRole("button", { name: "Entrar" })).toBeEnabled();
  };
  for (let i = 0; i < 5; i++) {
    await tentar();
    await expect(page.getByText("E-mail ou senha incorretos")).toBeVisible();
  }
  await tentar();
  await expect(page.getByText("Muitas tentativas sem sucesso")).toBeVisible();
});

test("Meus dados exige login; o pedido do usuário chega à TI, que responde", async ({ browser }) => {
  const anonimo = await novaPagina(browser);
  await anonimo.goto("/meus-dados");
  await expect(anonimo).toHaveURL(/\/login\?volta=%2Fmeus-dados/);
  const semLogin = await anonimo.request.get("/meus-dados/exportar", { maxRedirects: 0 });
  expect(semLogin.status()).toBe(307);

  const operador = await novaPagina(browser);
  await entrar(operador, USUARIOS.operador, /\/processos(\/|$)/);
  await operador.getByRole("link", { name: "Meus dados" }).click();
  await expect(operador.getByRole("heading", { level: 1, name: "Meus dados" })).toBeVisible();
  await expect(operador.getByText(USUARIOS.operador.email)).toBeVisible();
  const copia = await operador.request.get("/meus-dados/exportar");
  expect(copia.headers()["content-type"]).toContain("application/json");
  expect((await copia.json()).cadastro.email).toBe(USUARIOS.operador.email);

  const marca = `Pedido fictício ${randomUUID().slice(0, 8)}`;
  await operador.getByLabel("O que você pede").selectOption("CORRECAO");
  await operador.getByLabel("Descreva o pedido").fill(`${marca}: corrigir o nome.`);
  await operador.getByRole("button", { name: "Enviar pedido" }).click();
  await expect(operador.getByText("Pedido registrado.")).toBeVisible();

  const admin = await novaPagina(browser);
  await entrar(admin, USUARIOS.administrador, /\/admin(\/|$)/);
  await admin.getByRole("link", { name: "Pedidos LGPD" }).click();
  const item = admin.getByRole("listitem").filter({ hasText: marca });
  await item.getByLabel("Resposta ao usuário").fill("Nome corrigido (resposta fictícia).");
  await item.getByRole("button", { name: "Registrar resposta" }).click();
  // Respondido, o formulário dá lugar à resposta gravada.
  await expect(item.getByText("Nome corrigido (resposta fictícia).")).toBeVisible();
  await expect(item.getByLabel("Resposta ao usuário")).toHaveCount(0);

  await operador.reload();
  const meu = operador.getByRole("listitem").filter({ hasText: marca });
  await expect(meu.getByText("Nome corrigido (resposta fictícia).")).toBeVisible();
  await expect(meu.getByText("Respondido")).toBeVisible();
});
