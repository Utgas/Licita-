import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Pastas de src/ que o motor não pode importar (CLAUDE.md, regra 3; docs/arquitetura.md).
const PASTAS_PROIBIDAS_NO_MOTOR = ["app", "dados", "auth", "ia", "auditoria", "exportacao"];

// Módulos de sistema de arquivos, rede e processos, com e sem o prefixo "node:".
const MODULOS_NODE_PROIBIDOS_NO_MOTOR = [
  "fs",
  "fs/promises",
  "net",
  "http",
  "https",
  "http2",
  "dgram",
  "dns",
  "dns/promises",
  "tls",
  "child_process",
].flatMap((nome) => [nome, `node:${nome}`]);

const pastas = PASTAS_PROIBIDAS_NO_MOTOR.join("|");

const isolamentoDoMotor = {
  files: ["src/motor/**/*.{ts,tsx,js,jsx,mjs,cjs}"],
  rules: {
    "no-restricted-imports": [
      "error",
      {
        paths: MODULOS_NODE_PROIBIDOS_NO_MOTOR.map((name) => ({
          name,
          message: "src/motor é puro: sem sistema de arquivos nem rede.",
        })),
        patterns: [
          {
            regex: `^(@/|src/|(\\.\\./)+)(${pastas})(/|$)`,
            message: "src/motor não pode importar de app, dados, auth, ia, auditoria nem exportacao.",
          },
          {
            regex: "^(next|react|react-dom)(/|$)",
            message: "src/motor não depende de Next.js nem de React.",
          },
          {
            regex: "^@supabase/",
            message: "src/motor não depende do Supabase.",
          },
        ],
      },
    ],
    "no-restricted-globals": [
      "error",
      { name: "fetch", message: "src/motor é puro: sem rede." },
      { name: "XMLHttpRequest", message: "src/motor é puro: sem rede." },
      { name: "WebSocket", message: "src/motor é puro: sem rede." },
      { name: "Date", message: "src/motor é puro: a data entra como parâmetro." },
    ],
    "no-restricted-syntax": [
      "error",
      { selector: "ImportExpression", message: "src/motor não usa importação dinâmica." },
    ],
    "no-restricted-properties": [
      "error",
      { object: "Math", property: "random", message: "src/motor é puro: sem aleatoriedade." },
    ],
  },
};

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  isolamentoDoMotor,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
