import type { NextConfig } from "next";

const producao = process.env.NODE_ENV === "production";

/**
 * Cabeçalhos de segurança em toda resposta (decisão 0017). A página só carrega o que vem do próprio sistema
 * (arquitetura, "Recursos externos"), não abre dentro de outro site e não manda o endereço para fora. O Next põe
 * scripts na página, por isso o script-src aceita 'unsafe-inline'; em desenvolvimento, também 'unsafe-eval'.
 */
const politica = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${producao ? "" : " 'unsafe-eval'"}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "connect-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  ...(producao ? ["upgrade-insecure-requests"] : []),
].join("; ");

const CABECALHOS = [
  { key: "Content-Security-Policy", value: politica },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "same-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  ...(producao ? [{ key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" }] : []),
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  headers: async () => [{ source: "/:path*", headers: CABECALHOS }],
  /* config options here */
  cacheComponents: true,
  // O Word do checklist vai por ação do servidor; a Vercel aceita até 4,5 MB por requisição.
  experimental: { serverActions: { bodySizeLimit: "4mb" } },
  // O pacote de regras é lido do disco no servidor (src/dados/pacote.ts).
  outputFileTracingIncludes: { "/**": ["./regras/**/*"] },
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
