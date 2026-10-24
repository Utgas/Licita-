/**
 * Fluxo inteiro de um TR fictício (Marco 2, passo 14): login, novo processo, envio do Word fictício, resolução da
 * trava, itens, wizard, minuta sem travas, cópia de todas as seções, PDF e conclusão. Depois, o operador de outra OM
 * não vê o processo. Precisa do Supabase local preparado por testes/telas/preparar.ts.
 */
import { readFileSync } from "node:fs";
import { type Page, expect, test } from "@playwright/test";
import { USUARIOS } from "./usuarios.ts";
import { wordFicticioCompleto } from "./word-ficticio.ts";

const NUMERO = `00000.${String(Date.now()).slice(-6)}/2026-01`;
const OBJETO = "Aquisição fictícia de luvas de procedimento";

async function entrar(page: Page, usuario: { email: string; senha: string }) {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(usuario.email);
  await page.getByLabel("Senha").fill(usuario.senha);
  await page.getByRole("button", { name: "Entrar" }).click();
  try {
    await page.waitForURL(/\/processos(\/|$)/, { timeout: 30000 });
  } catch (e) {
    // Diagnóstico no log do CI: onde a página parou e o que ela mostra.
    console.log(`Login não saiu de ${page.url()}:\n${await page.locator("body").innerText()}`);
    throw e;
  }
}

let urlDoProcesso = "";

test.describe.configure({ mode: "serial" });

test("fluxo completo de um TR fictício, do login ao PDF", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await entrar(page, USUARIOS.operador);

  // Novo processo
  await page.goto("/processos/novo");
  await page.getByLabel("Número do processo (NUP)").fill(NUMERO);
  await page.getByLabel("Objeto (resumo)").fill(OBJETO);
  await page.getByLabel("Pregão").check();
  await page.getByRole("group", { name: "Registro de preços?" }).getByLabel("Não").check();
  await page.getByLabel("Consumo").check();
  await page.getByRole("button", { name: "Criar processo" }).click();
  await page.waitForURL(/\/processos\/[0-9a-f-]{36}\/checklist/);
  urlDoProcesso = page.url().replace(/\/checklist.*$/, "");

  // Checklist: envio do Word e resolução da trava (duas marcas na 3.3)
  await page.locator('input[type="file"][name="arquivo"]').setInputFiles({ name: "checklist-ficticio.docx", mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document", buffer: await wordFicticioCompleto(NUMERO) });
  await page.getByRole("button", { name: "Ler o checklist" }).click();
  await expect(page.getByText(/Checklist de consumo lido/)).toBeVisible();
  const trava = page.locator("li", { hasText: "CK-C-3.3" }).filter({ has: page.getByText("Trava", { exact: true }) }).first();
  await expect(trava).toBeVisible();
  await trava.getByRole("button", { name: "Não", exact: true }).click();
  await expect(page.locator("li", { hasText: "CK-C-3.3" }).filter({ has: page.getByText("Trava", { exact: true }) })).toHaveCount(0);
  // As demais (resposta única para vários itens) o operador confere e confirma como estão.
  for (let vez = 0; vez < 10 && (await page.getByText("Nenhuma trava", { exact: false }).count()) === 0; vez++) {
    const travas = await page.getByRole("heading", { name: /^Travas \(\d+\)$/ }).innerText();
    await page.getByRole("button", { name: "Conferi: vale como está" }).first().click();
    await expect(page.getByRole("heading", { name: /^Travas \(\d+\)$/ })).not.toHaveText(travas);
  }
  await expect(page.getByText("Nenhuma trava", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Seguir para os itens" }).click();
  await page.waitForURL(/\/itens$/);

  // Itens: um item digitado
  await page.locator("summary", { hasText: "Incluir item" }).click();
  const item = page.locator("details", { has: page.locator("summary", { hasText: "Incluir item" }) });
  await item.locator('input[name="numero"]').fill("1");
  await item.locator('input[name="especificacao"]').fill("Luva de procedimento fictícia, tamanho M");
  await item.locator('input[name="catmat"]').fill("000000");
  await item.locator('input[name="unidadeMedida"]').fill("caixa");
  await item.locator('input[name="quantidade"]').fill("100");
  await item.locator('input[name="valorUnitario"]').fill("20,00");
  await item.locator('select[name="categoria"]').selectOption("CONSUMO");
  await item.locator('select[name="exigeAmostra"]').selectOption("N");
  await item.locator('select[name="controleEspecial"]').selectOption("N");
  await item.getByRole("button", { name: "Incluir item" }).click();
  await expect(page.getByText("Item 1 salvo.")).toBeVisible();
  await expect(page.getByText(/ME\/EPP: Exclusivo/)).toBeVisible();
  await page.getByRole("button", { name: "Seguir para o wizard" }).click();
  await page.waitForURL(/\/wizard$/);

  // Wizard: responde cada pergunta pendente (primeira opção, ou texto fictício) até não sobrar nenhuma
  for (let vez = 0; vez < 80; vez++) {
    const titulo = await page.getByRole("heading", { name: /^Perguntas \d+ sem resposta$/ }).innerText();
    if (/\b0 sem resposta$/.test(titulo)) break;
    const pergunta = page.locator("section[aria-live]");
    const opcoes = pergunta.locator('input[name="valor"][type="radio"], input[name="valor"][type="checkbox"]');
    if ((await opcoes.count()) > 0) await opcoes.first().check();
    else await pergunta.locator('textarea[name="valor"]').fill("30");
    const justificativa = pergunta.locator('textarea[name="justificativa"]');
    if ((await justificativa.count()) > 0) await justificativa.fill("Justificativa fictícia para o teste.");
    const antes = page.url();
    await pergunta.getByRole("button", { name: "Salvar e ir para a próxima" }).click();
    await page.waitForURL((u) => u.toString() !== antes);
  }
  await expect(page.getByRole("heading", { name: "Perguntas 0 sem resposta" })).toBeVisible();

  // Dados que as validações de bloqueio pedem, quando faltam: número do processo (sugerido; o Word fictício já o
  // traz no cabeçalho) e versão do modelo AGU
  const campo = (id: string) => page.locator("li", { has: page.getByRole("button", { name: `Salvar ${id}` }) });
  for (const [id, valor] of [["VAR-001", null], ["VAR-099", "DEZ/2025"]] as const) {
    if ((await campo(id).getByText(/Falta em/).count()) === 0) continue;
    if (valor) await campo(id).getByLabel(/Valor/).fill(valor);
    await campo(id).getByRole("button", { name: `Salvar ${id}` }).click();
    await expect(campo(id).getByText(`Feito: ${id} salva.`)).toBeVisible();
  }
  await page.getByRole("button", { name: "Seguir para a minuta" }).click();
  await page.waitForURL(/\/revisao$/);

  // Minuta sem travas; um trecho mostra a origem
  await expect(page.getByText("Sem travas: a minuta pode ser exportada")).toBeVisible();
  await page.locator("article details").nth(3).locator("summary").click();
  await expect(page.locator("article details[open]").getByText(/Bloco TR-/)).toBeVisible();
  await page.getByRole("button", { name: "Seguir para exportar" }).click();
  await page.waitForURL(/\/exportar$/);

  // Cópia de todas as seções, uma por uma
  const linhas = page.locator("main ol > li", { has: page.locator("summary", { hasText: "Ver o texto" }) });
  await expect(linhas.first()).toBeVisible();
  const secoes = await linhas.count();
  expect(secoes).toBeGreaterThan(10);
  for (let k = 0; k < secoes; k++) {
    await linhas.nth(k).getByRole("button", { name: "Copiar", exact: true }).click();
    await expect(linhas.nth(k).getByText("Copiado", { exact: true })).toBeVisible();
    await expect(linhas.nth(k).getByRole("button", { name: "Copiar", exact: true })).toBeEnabled();
  }
  expect(await page.evaluate(() => navigator.clipboard.readText())).not.toBe("");

  // PDF
  const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: "Baixar o PDF da minuta" }).click()]);
  const pdf = readFileSync((await download.path()) as string);
  expect(pdf.subarray(0, 5).toString()).toBe("%PDF-");
  await page.reload();
  await expect(page.getByText(/PDF baixado 1 vez/)).toBeVisible();
  await expect(page.getByText(`${secoes} de ${secoes} copiadas`)).toBeVisible();

  // ETP (Marco 3): o mesmo processo, campo a campo; a equipe informa um dado, copia o campo e baixa o PDF
  await page.getByRole("link", { name: "ETP", exact: true }).click();
  await page.waitForURL(/\/etp$/);
  await expect(page.getByRole("heading", { name: /Descrição da necessidade da contratação/ })).toBeVisible();
  const viabilidade = page.locator("section", { has: page.locator("h3", { hasText: "Justificativa da viabilidade" }) });
  const texto = "Contratação fictícia viável, pelas seções anteriores deste estudo.";
  await viabilidade.getByLabel("Valor").fill(texto);
  await viabilidade.getByRole("button", { name: "Salvar VAR-108" }).click();
  await expect(viabilidade.locator("p", { hasText: texto })).toBeVisible();
  await viabilidade.getByRole("button", { name: "Copiar", exact: true }).click();
  await expect(viabilidade.getByText("Copiado", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(texto);
  const [pdfDoEtp] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: "Baixar o PDF do ETP" }).click()]);
  expect(readFileSync((await pdfDoEtp.path()) as string).subarray(0, 5).toString()).toBe("%PDF-");
  await page.reload();
  await expect(viabilidade.getByText("Copiado", { exact: true })).toBeVisible();
  // A minuta do TR mostra de que campo do ETP vem cada trecho derivado (M06)
  await page.goto(`${urlDoProcesso}/revisao`);
  await expect(page.locator("article details", { hasText: "Repete o ETP" }).first()).toBeAttached();
  await page.goto(`${urlDoProcesso}/exportar`);
  await expect(page.getByText(`${secoes} de ${secoes} copiadas`)).toBeVisible();

  // Conclusão
  await page.getByLabel(/Confirmo que a minuta foi copiada e revisada/).check();
  await page.getByRole("button", { name: "Marcar como concluído" }).click();
  await expect(page.getByText(/Processo concluído em/)).toBeVisible();
  await page.goto("/processos");
  await expect(page.locator("main")).toContainText(NUMERO);
  await expect(page.locator("main")).toContainText("Será apagado em");
});

test("operador de outra OM não vê o processo", async ({ page }) => {
  expect(urlDoProcesso).not.toBe("");
  await entrar(page, USUARIOS.operadorOutraOm);
  await expect(page.locator("main")).not.toContainText(NUMERO);
  await page.goto(`${urlDoProcesso}/revisao`);
  await expect(page.getByText(OBJETO)).toHaveCount(0);
  await expect(page.getByText(/could not be found|não encontrad/i)).toBeVisible();
});
