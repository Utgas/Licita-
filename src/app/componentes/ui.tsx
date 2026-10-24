/**
 * Peças visuais comuns (decisão 0014): selo de estado, aviso, título de seção e classes de botão. Cada estado tem
 * cor, ícone e texto; nenhum depende só da cor. Servem a telas de servidor e de cliente.
 */
import type { ReactNode } from "react";
import { Icone, type NomeDoIcone } from "./icones.tsx";

export type TipoDeEstado = "trava" | "atencao" | "ok" | "padrao" | "neutro" | "vazio" | "juridica" | "calculada" | "pendente";

const ESTILO: Record<TipoDeEstado, { classe: string; icone: NomeDoIcone }> = {
  trava: { classe: "border-trava/40 bg-trava-fundo text-trava", icone: "trava" },
  atencao: { classe: "border-atencao/30 bg-atencao-fundo text-atencao", icone: "atencao" },
  ok: { classe: "border-ok/30 bg-ok-fundo text-ok", icone: "ok" },
  padrao: { classe: "border-padrao/30 bg-padrao-fundo text-padrao", icone: "padrao" },
  neutro: { classe: "border-linha bg-folha text-tinta-2", icone: "documento" },
  vazio: { classe: "border-linha bg-folha text-tinta-2", icone: "vazio" },
  juridica: { classe: "border-trava/40 bg-trava-fundo text-trava", icone: "juridica" },
  calculada: { classe: "border-linha bg-papel text-tinta-2", icone: "calculada" },
  pendente: { classe: "border-atencao/30 bg-atencao-fundo text-atencao", icone: "pendente" },
};

/** Selo de estado: ícone e texto curto, na cor do estado. */
export function Selo({ tipo, children }: { tipo: TipoDeEstado; children: ReactNode }) {
  const e = ESTILO[tipo];
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-sm border px-2 py-0.5 text-sm font-medium ${e.classe}`}>
      <Icone nome={e.icone} tamanho={15} />
      {children}
    </span>
  );
}

const AVISO: Record<"trava" | "atencao" | "ok" | "info", { classe: string; icone: NomeDoIcone }> = {
  trava: { classe: "border-l-trava bg-trava-fundo text-trava", icone: "trava" },
  atencao: { classe: "border-l-atencao bg-atencao-fundo text-atencao", icone: "atencao" },
  ok: { classe: "border-l-ok bg-ok-fundo text-ok", icone: "ok" },
  info: { classe: "border-l-tinta-2 bg-folha text-tinta", icone: "documento" },
};

/** Aviso em faixa: barra lateral na cor do estado, ícone, título e texto. */
export function Aviso({ tipo, titulo, children }: { tipo: keyof typeof AVISO; titulo: ReactNode; children?: ReactNode }) {
  const a = AVISO[tipo];
  return (
    <div role={tipo === "trava" ? "alert" : undefined} className={`flex gap-3 border border-l-4 border-linha p-4 ${a.classe}`}>
      <Icone nome={a.icone} tamanho={20} className="mt-0.5" />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <p className="font-semibold">{titulo}</p>
        {children && <div className="flex flex-col gap-1.5 text-[0.95rem] text-tinta">{children}</div>}
      </div>
    </div>
  );
}

/** Título de seção: texto e, à direita, um complemento (contagem, ação). */
export function TituloDeSecao({ children, complemento, nivel = 2 }: { children: ReactNode; complemento?: ReactNode; nivel?: 2 | 3 }) {
  const Tag = nivel === 2 ? "h2" : "h3";
  return (
    <div className="flex flex-wrap items-end justify-between gap-2 border-b border-linha pb-2">
      <Tag className={nivel === 2 ? "text-lg font-semibold" : "font-semibold"}>{children}</Tag>
      {complemento && <div className="text-sm text-tinta-2">{complemento}</div>}
    </div>
  );
}

/** Classes de botão (também para link com cara de botão). Alvo de 44 px. */
export function classesDoBotao(variante: "principal" | "secundario" | "discreto" = "principal"): string {
  const base = "inline-flex min-h-11 items-center justify-center gap-2 rounded-sm px-4 font-medium transition-colors disabled:opacity-60";
  if (variante === "principal") return `${base} bg-acao text-folha hover:bg-acao-escura`;
  if (variante === "secundario") return `${base} border border-linha-forte bg-folha text-tinta hover:bg-realce`;
  return `${base} px-2 text-tinta underline hover:bg-realce`;
}

/** Campo de texto: mesma caixa em todo o sistema. */
export const CLASSE_DA_CAIXA = "min-h-11 w-full rounded-sm border border-linha-forte bg-folha px-3 text-base font-normal text-tinta";

/** Código do pacote (WZ-03, VAR-034, hash) em fonte de código. */
export function Codigo({ children }: { children: ReactNode }) {
  return <span className="font-mono text-[0.9em] tracking-tight">{children}</span>;
}
