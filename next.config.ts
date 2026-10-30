import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  // O Word do checklist vai por ação do servidor; a Vercel aceita até 4,5 MB por requisição.
  experimental: { serverActions: { bodySizeLimit: "4mb" } },
  // O pacote de regras é lido do disco no servidor (src/dados/pacote.ts).
  // O worker do pdfjs-dist é importado em tempo de execução e o rastreador não o vê (decisão 0017).
  outputFileTracingIncludes: { "/**": ["./regras/**/*", "./node_modules/pdfjs-dist/legacy/build/pdf.worker.mjs"] },
  // Leitura do checklist em PDF (decisão 0017): o pdfjs-dist roda do node_modules, sem passar pelo bundler. O
  // @napi-rs/canvas (opcional, só para desenhar página) fica fora da função.
  serverExternalPackages: ["pdfjs-dist"],
  outputFileTracingExcludes: { "/**": ["./node_modules/@napi-rs/**/*"] },
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
