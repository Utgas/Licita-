import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import Link from "next/link";
import { AvisoDeCookies } from "./componentes/aviso-cookies.tsx";
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
      <body className="flex min-h-full flex-col bg-papel text-tinta">
        {/* Primeiro item do Tab: pula o cabeçalho e vai direto ao conteúdo de cada tela. */}
        <a href="#conteudo" className="sr-only z-50 bg-folha p-3 text-tinta underline focus:not-sr-only focus:fixed focus:left-2 focus:top-2">
          Pular para o conteúdo
        </a>
        {children}
        <footer className="mt-auto border-t border-linha">
          <nav aria-label="Informações legais" className="mx-auto flex w-full max-w-[1400px] flex-wrap gap-x-4 px-4 py-2 text-sm md:px-6">
            <Link href="/privacidade" className="flex min-h-11 items-center text-tinta-2 underline hover:text-tinta">
              Política de Privacidade
            </Link>
            <Link href="/privacidade#cookies" className="flex min-h-11 items-center text-tinta-2 underline hover:text-tinta">
              Cookies
            </Link>
            <Link href="/termos" className="flex min-h-11 items-center text-tinta-2 underline hover:text-tinta">
              Termos de Uso
            </Link>
          </nav>
        </footer>
        <AvisoDeCookies />
      </body>
    </html>
  );
}
