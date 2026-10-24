import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
