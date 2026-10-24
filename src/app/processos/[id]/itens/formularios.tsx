"use client";
/** Formulários da tela dos itens: importação, item a item e respostas dadas aqui. */
import { useActionState } from "react";
import type { Resultado } from "@/auth/acoes.ts";
import { Botao, Mensagem } from "../../../componentes/formulario.tsx";

type Acao = (anterior: Resultado, dados: FormData) => Promise<Resultado>;
export type ColunaDoFormulario = { titulo: string; coluna: string; tipo: string; obrigatoria?: boolean };

const caixa = "min-h-11 w-full rounded-sm border border-linha-forte px-3";

export function Importar({ acao }: { acao: Acao }) {
  const [resultado, enviar] = useActionState(acao, null);
  return (
    <form action={enviar} className="flex flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm font-medium">
        Planilha de itens (.xlsx, no modelo)
        <input type="file" name="planilha" accept=".xlsx" required className="min-h-11 font-normal" />
      </label>
      <Mensagem resultado={resultado} />
      <div>
        <Botao>Importar e substituir a tabela</Botao>
      </div>
    </form>
  );
}

export function FormularioItem({ acao, apagar, colunas, valores }: { acao: Acao; apagar?: Acao; colunas: ColunaDoFormulario[]; valores?: Record<string, string> }) {
  const [resultado, salvar] = useActionState(acao, null);
  const [apagado, apagarAcao] = useActionState(apagar ?? (async () => null), null);
  return (
    <div className="flex flex-col gap-2">
      <form action={salvar} className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {valores && <input type="hidden" name="original" value={valores.numero} />}
        {colunas.map((c) => (
          <label key={c.coluna} className={`flex flex-col gap-1 text-sm font-medium ${c.coluna === "especificacao" || c.coluna === "justificativaExcecaoMeEpp" ? "sm:col-span-2 lg:col-span-3" : ""}`}>
            {c.titulo}
            {c.obrigatoria ? " *" : ""}
            {c.tipo === "SN" || c.tipo === "categoria" ? (
              <select name={c.coluna} defaultValue={valores?.[c.coluna] ?? ""} className={caixa}>
                <option value="">—</option>
                {(c.tipo === "SN" ? ["S", "N"] : ["CONSUMO", "PERMANENTE"]).map((o) => (
                  <option key={o} value={o}>
                    {o === "S" ? "Sim" : o === "N" ? "Não" : o === "CONSUMO" ? "Consumo" : "Permanente"}
                  </option>
                ))}
              </select>
            ) : (
              <input name={c.coluna} defaultValue={valores?.[c.coluna] ?? ""} inputMode={c.tipo === "texto" ? "text" : "decimal"} className={caixa} />
            )}
          </label>
        ))}
        <div className="flex flex-col gap-2 sm:col-span-2 lg:col-span-3">
          <Mensagem resultado={resultado} />
          <div>
            <Botao>{valores ? "Salvar item" : "Incluir item"}</Botao>
          </div>
        </div>
      </form>
      {valores && apagar && (
        <form action={apagarAcao}>
          <input type="hidden" name="numero" value={valores.numero} />
          <Mensagem resultado={apagado} />
          <Botao variante="secundario">Apagar este item</Botao>
        </form>
      )}
    </div>
  );
}

export function RespostaAqui({ acao, pergunta, rotulo, tipo, valor, ajuda }: { acao: Acao; pergunta: string; rotulo: string; tipo: "simnao" | "numero"; valor: string; ajuda?: string }) {
  const [resultado, salvar] = useActionState(acao, null);
  return (
    <form action={salvar} className="flex flex-col gap-2">
      <input type="hidden" name="pergunta" value={pergunta} />
      {tipo === "simnao" ? (
        <fieldset className="flex flex-wrap gap-4">
          <legend className="text-sm font-medium">{rotulo}</legend>
          {[
            ["SIM", "Sim"],
            ["NAO", "Não"],
          ].map(([v, r]) => (
            <label key={v} className="flex min-h-11 items-center gap-2">
              <input type="radio" name="valor" value={v} defaultChecked={valor === v} className="size-5" /> {r}
            </label>
          ))}
        </fieldset>
      ) : (
        <label className="flex flex-col gap-1 text-sm font-medium">
          {rotulo}
          <input name="valor" defaultValue={valor} inputMode="decimal" className={`${caixa} max-w-40`} />
        </label>
      )}
      {ajuda && <p className="text-sm text-tinta-2">{ajuda}</p>}
      <Mensagem resultado={resultado} />
      <div>
        <Botao variante="secundario">Salvar</Botao>
      </div>
    </form>
  );
}
