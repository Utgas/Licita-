import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

// Fontes baixadas no build e servidas pelo próprio sistema (next/font): nenhuma página busca fonte de terceiros.
const texto = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--fonte-texto", display: "swap" });
const codigo = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--fonte-codigo", display: "swap" });

export const metadata: Metadata = {
  title: "Licita+",
  description: "Minutas de Termo de Referência no modelo AGU",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${texto.variable} ${codigo.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-papel text-tinta">{children}</body>
    </html>
  );
}
