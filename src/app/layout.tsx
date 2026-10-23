import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Licita+",
  description: "Minutas de Termo de Referência no modelo AGU",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
