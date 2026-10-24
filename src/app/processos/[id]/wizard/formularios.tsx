"use client";
/** Formulários do wizard: uma pergunta por vez e campo extra (VAR). */
import { useActionState } from "react";
import type { Resultado } from "@/auth/acoes.ts";
import { Botao, Mensagem } from "../../../componentes/formulario.tsx";

type Acao = (anterior: Resultado, dados: FormData) => Promise<Resultado>;
const caixa = "min-h-11 w-full rounded border border-zinc-500 px-3 py-2";

export type DadosDaPerguntaWz = {
  id: string;
  tipo: string;
  opcoes: { valor: string; rotulo: string }[];
  valor: unknown;
  justificativa: string;
  regraJustificativa: string | null;
  sugestao: { valor: unknown; perguntas: string } | null;
  proxima: string;
};

export function PerguntaWizard({ acao, d }: { acao: Acao; d: DadosDaPerguntaWz }) {
  const [resultado, salvar] = useActionState(acao, null);
  const [r2, aceitar] = useActionState(acao, null);
  const marcadas = new Set((Array.isArray(d.valor) ? d.valor : d.valor === null || d.valor === undefined ? [] : [d.valor]).map(String));
  const mostrar = (v: unknown) => (Array.isArray(v) ? v.join(", ") : String(v));
  return (
    <div className="flex flex-col gap-4">
      {d.sugestao && (
        <div className="flex flex-col gap-2 rounded border-2 border-dashed border-blue-800 bg-blue-50 p-3">
          <p>
            <strong>Sugestão do checklist</strong> ({d.sugestao.perguntas}): {mostrar(d.sugestao.valor)}. É só uma sugestão: a decisão é da equipe.
          </p>
          <form action={aceitar}>
            <input type="hidden" name="pergunta" value={d.id} />
            <input type="hidden" name="origem" value="SUGESTAO_ACEITA" />
            <input type="hidden" name="proxima" value={d.proxima} />
            {(Array.isArray(d.sugestao.valor) ? d.sugestao.valor : [d.sugestao.valor]).map((v) => (
              <input key={String(v)} type="hidden" name="valor" value={String(v)} />
            ))}
            <Mensagem resultado={r2} />
            <Botao variante="secundario">Aceitar a sugestão</Botao>
          </form>
        </div>
      )}
      <form action={salvar} className="flex flex-col gap-4">
        <input type="hidden" name="pergunta" value={d.id} />
        <input type="hidden" name="proxima" value={d.proxima} />
        {d.opcoes.length > 0 ? (
          <fieldset className="flex flex-col gap-1">
            <legend className="text-sm font-medium">{d.tipo === "MULTIPLA" ? "Marque todas as que valem" : "Resposta"}</legend>
            {d.opcoes.map((o) => (
              <label key={o.valor} className="flex min-h-11 items-center gap-3">
                <input type={d.tipo === "MULTIPLA" ? "checkbox" : "radio"} name="valor" value={o.valor} defaultChecked={marcadas.has(o.valor)} className="size-5" /> {o.rotulo}
              </label>
            ))}
          </fieldset>
        ) : (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Resposta
            <textarea name="valor" defaultValue={marcadas.size ? mostrar(d.valor) : ""} rows={d.tipo === "TEXTO" ? 3 : 1} className={caixa} />
          </label>
        )}
        {d.regraJustificativa && (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Justificativa
            <span className="font-normal text-zinc-700">Quando é exigida: {d.regraJustificativa}</span>
            <textarea name="justificativa" defaultValue={d.justificativa} rows={3} className={caixa} />
          </label>
        )}
        <Mensagem resultado={resultado} />
        <div>
          <Botao>Salvar e seguir</Botao>
        </div>
      </form>
    </div>
  );
}

export function CampoExtra({ acao, variavel, rotulo, ajuda, tipo, valor }: { acao: Acao; variavel: string; rotulo: string; ajuda: string; tipo: string; valor: string }) {
  const [resultado, salvar] = useActionState(acao, null);
  return (
    <form action={salvar} className="flex flex-col gap-1">
      <input type="hidden" name="variavel" value={variavel} />
      <label className="flex flex-col gap-1 text-sm font-medium">
        {variavel} · {rotulo}
        {tipo === "TEXTO" || tipo === "TABELA" ? (
          <textarea name="valor" defaultValue={valor} rows={2} className={caixa} />
        ) : (
          <input name="valor" defaultValue={valor} type={tipo === "DATA" ? "date" : "text"} inputMode={tipo === "NUMERO" || tipo === "MOEDA" ? "decimal" : "text"} className={`${caixa} max-w-md`} />
        )}
      </label>
      {ajuda && <span className="text-sm text-zinc-700">{ajuda}</span>}
      <Mensagem resultado={resultado} />
      <div>
        <Botao variante="secundario">Salvar</Botao>
      </div>
    </form>
  );
}
