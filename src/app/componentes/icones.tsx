/**
 * Ícones do Licita+ (decisão 0014): conjunto próprio e pequeno, traço de 1,75 px em grade de 20 px, cantos retos.
 * Desenhados para o que o sistema faz (trava, destaque, lacuna, valor padrão, decisão jurídica), sem biblioteca
 * de terceiros. Sempre acompanham um texto; sozinhos levam rótulo (aria-label) para leitor de tela.
 */
import type { ReactNode } from "react";

const DESENHOS = {
  /** Trava: cadeado. */
  trava: (
    <>
      <rect x="4" y="9" width="12" height="8.5" />
      <path d="M6.5 9V6.5a3.5 3.5 0 0 1 7 0V9" />
      <path d="M10 12.2v2.4" />
    </>
  ),
  /** Atenção: losango de sinalização com exclamação. */
  atencao: (
    <>
      <path d="M10 2.5 17.5 10 10 17.5 2.5 10Z" />
      <path d="M10 6.8v4.2" />
      <path d="M10 13.2v.6" />
    </>
  ),
  /** Ok: quadrado marcado, como a caixa do checklist em papel. */
  ok: (
    <>
      <rect x="3" y="3" width="14" height="14" />
      <path d="m6.5 10.2 2.4 2.4 4.6-5.2" />
    </>
  ),
  /** Sem resposta: caixa vazia. */
  vazio: <rect x="3" y="3" width="14" height="14" />,
  /** Lacuna: colchetes com o espaço a preencher. */
  lacuna: (
    <>
      <path d="M6 4H3.5v12H6" />
      <path d="M14 4h2.5v12H14" />
      <path d="M7.5 13h5" />
    </>
  ),
  /** Valor padrão: etiqueta do pacote. */
  padrao: (
    <>
      <path d="M3 3h7.2l6.8 6.8-7.2 7.2L3 10.2Z" />
      <path d="M6.6 6.6h.01" />
    </>
  ),
  /** Calculada pelos itens: quadro com igual. */
  calculada: (
    <>
      <rect x="3" y="3" width="14" height="14" />
      <path d="M6.5 8.5h7M6.5 11.5h7" />
    </>
  ),
  /** Decisão jurídica: balança. */
  juridica: (
    <>
      <path d="M10 3v13.5M6 16.5h8" />
      <path d="M4 6h12" />
      <path d="m4 6-2 5h4Z" />
      <path d="m16 6-2 5h4Z" />
    </>
  ),
  /** Sugestão do checklist: balão de fala. */
  sugestao: (
    <>
      <path d="M3 4h14v9H9l-4 3v-3H3Z" />
      <path d="M7 8.5h6" />
    </>
  ),
  /** Pendente: círculo vazio. */
  pendente: <circle cx="10" cy="10" r="6.5" />,
  copiar: (
    <>
      <rect x="6.5" y="6.5" width="10" height="10.5" />
      <path d="M13.5 6.5V3H3.5v10.5h3" />
    </>
  ),
  baixar: (
    <>
      <path d="M10 3v9.5M6 8.8l4 3.7 4-3.7" />
      <path d="M3.5 13.5V17h13v-3.5" />
    </>
  ),
  documento: (
    <>
      <path d="M4.5 2.5h7.5l3.5 3.5v11.5h-11Z" />
      <path d="M12 2.5V6h3.5" />
      <path d="M7 10h6M7 13h6" />
    </>
  ),
  avancar: <path d="M4 10h11.5M11 5.5l4.5 4.5-4.5 4.5" />,
  voltar: <path d="M16 10H4.5M9 5.5 4.5 10 9 14.5" />,
  sair: (
    <>
      <path d="M11.5 3.5h-8v13h8" />
      <path d="M8 10h9M14 7l3 3-3 3" />
    </>
  ),
  mais: <path d="M10 4v12M4 10h12" />,
  busca: (
    <>
      <circle cx="8.5" cy="8.5" r="5" />
      <path d="m12.2 12.2 4.3 4.3" />
    </>
  ),
  origem: (
    <>
      <path d="M3 5h9M3 10h6M3 15h9" />
      <circle cx="15" cy="10" r="2.2" />
    </>
  ),
} satisfies Record<string, ReactNode>;

export type NomeDoIcone = keyof typeof DESENHOS;

export function Icone({ nome, tamanho = 18, rotulo, className = "" }: { nome: NomeDoIcone; tamanho?: number; rotulo?: string; className?: string }) {
  return (
    <svg
      viewBox="0 0 20 20"
      width={tamanho}
      height={tamanho}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="square"
      strokeLinejoin="miter"
      role={rotulo ? "img" : undefined}
      aria-label={rotulo}
      aria-hidden={rotulo ? undefined : true}
      className={`inline-block shrink-0 ${className}`}
    >
      {DESENHOS[nome]}
    </svg>
  );
}
