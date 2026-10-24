"use client";
/** Formulários da tela do wizard: uma pergunta por vez e os campos extras que a minuta pede. */
import { useActionState, useState } from "react";
import type { Resultado } from "@/auth/acoes.ts";
import { Botao, Mensagem } from "../../../componentes/formulario.tsx";

type Acao = (anterior: Resultado, dados: FormData) => Promise<Resultado>;
const caixa = "min-h-11 w-full rounded-sm border border-linha-forte px-3";

export type DadosDaPergunta = {
  id: string;
  tipo: string;
  opcoes: { codigo: string; rotulo: string }[];
  orientacao: string;
  valor: string[];
  /** Há resposta gravada pela equipe (o que veio do checklist não se apaga aqui). */
  daEquipe: boolean;
  justificativa: { texto: string; obrigatoriaCom: "sempre" | string[] } | null;
  justificativaAtual: string;
};

export function FormularioPergunta({ acao, limpar, d }: { acao: Acao; limpar: Acao; d: DadosDaPergunta }) {
  const [resultado, salvar] = useActionState(acao, null);
  const [limpo, limparAcao] = useActionState(limpar, null);
  const [escolhidos, setEscolhidos] = useState<string[]>(d.valor);
  const j = d.justificativa;
  const obrigatoria = j !== null && (j.obrigatoriaCom === "sempre" || escolhidos.some((v) => j.obrigatoriaCom.includes(v)));
  const multipla = d.tipo === "MULTIPLA";
  return (
    <div className="flex flex-col gap-3">
      <form action={salvar} className="flex flex-col gap-3">
        <input type="hidden" name="pergunta" value={d.id} />
        {d.opcoes.length > 0 ? (
          <fieldset className="flex flex-col gap-1">
            <legend className="sr-only">Resposta</legend>
            {d.opcoes.map((o) => (
              <label key={o.codigo} className="flex min-h-11 items-center gap-3">
                <input
                  type={multipla ? "checkbox" : "radio"}
                  name="valor"
                  value={o.codigo}
                  defaultChecked={d.valor.includes(o.codigo)}
                  onChange={(e) => setEscolhidos(multipla ? (e.target.checked ? [...escolhidos, o.codigo] : escolhidos.filter((x) => x !== o.codigo)) : [o.codigo])}
                  className="size-5"
                />
                {o.rotulo}
              </label>
            ))}
          </fieldset>
        ) : (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Resposta
            <textarea name="valor" defaultValue={d.valor[0] ?? ""} rows={3} className={`${caixa} py-2 text-base font-normal`} />
            {d.orientacao && <span className="font-normal text-tinta-2">Informe: {d.orientacao}</span>}
          </label>
        )}
        {j && (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Justificativa {obrigatoria ? "(obrigatória para esta resposta)" : "(se a resposta pedir)"}
            <textarea name="justificativa" defaultValue={d.justificativaAtual} rows={3} required={obrigatoria} className={`${caixa} py-2 text-base font-normal`} />
            <span className="font-normal text-tinta-2">{j.texto}</span>
          </label>
        )}
        <Mensagem resultado={resultado} />
        <div>
          <Botao>Salvar e ir para a próxima</Botao>
        </div>
      </form>
      {d.daEquipe && (
        <form action={limparAcao}>
          <input type="hidden" name="pergunta" value={d.id} />
          <Mensagem resultado={limpo} />
          <Botao variante="secundario">Apagar a resposta da equipe</Botao>
        </form>
      )}
    </div>
  );
}

/** Aceita a sugestão do checklist como resposta (origem SUGESTAO_ACEITA). */
export function AceitarSugestao({ acao, pergunta, valor, rotulo }: { acao: Acao; pergunta: string; valor: string[]; rotulo: string }) {
  const [resultado, salvar] = useActionState(acao, null);
  return (
    <form action={salvar} className="flex flex-col gap-2">
      <input type="hidden" name="pergunta" value={pergunta} />
      <input type="hidden" name="origem" value="SUGESTAO_ACEITA" />
      {valor.map((v) => (
        <input key={v} type="hidden" name="valor" value={v} />
      ))}
      <Mensagem resultado={resultado} />
      <div>
        <Botao variante="secundario">Aceitar a sugestão: {rotulo}</Botao>
      </div>
    </form>
  );
}

export type DadosDoCampo = {
  id: string;
  descricao: string;
  validacao: string;
  codigos: string[];
  forma: { tipo: "simples"; numerico: boolean; data: boolean } | { tipo: "lista" } | { tipo: "partes"; partes: { caminho: string; numerico: boolean }[] } | { tipo: "tabela"; colunas: { campo: string; cabecalho: string }[] };
  valores: Record<string, string>;
  falta: boolean;
  /** Texto corrido (campo do ETP): caixa de várias linhas. */
  multilinha?: boolean;
};

export function FormularioCampo({ acao, c }: { acao: Acao; c: DadosDoCampo }) {
  const [resultado, salvar] = useActionState(acao, null);
  const f = c.forma;
  return (
    <form action={salvar} className="flex flex-col gap-2">
      <input type="hidden" name="campo" value={c.id} />
      {f.tipo === "simples" &&
        (c.codigos.length ? (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Valor
            <select name="valor" defaultValue={c.valores.valor ?? ""} className={caixa}>
              <option value="">—</option>
              {c.codigos.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </label>
        ) : c.multilinha && !f.numerico && !f.data ? (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Valor
            <textarea name="valor" defaultValue={c.valores.valor ?? ""} rows={5} className={`${caixa} py-2 text-base font-normal`} />
          </label>
        ) : (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Valor{f.numerico ? " (número)" : f.data ? " (DD/MM/AAAA)" : ""}
            <input name="valor" defaultValue={c.valores.valor ?? ""} inputMode={f.numerico ? "decimal" : "text"} className={caixa} />
          </label>
        ))}
      {(f.tipo === "lista" || f.tipo === "tabela") && (
        <label className="flex flex-col gap-1 text-sm font-medium">
          {f.tipo === "lista" ? "Um por linha" : `Uma linha por linha da tabela; colunas separadas por ";": ${f.colunas.map((x) => x.cabecalho || x.campo).join("; ")}`}
          <textarea name="valor" defaultValue={c.valores.valor ?? ""} rows={4} className={`${caixa} py-2 text-base font-normal`} />
        </label>
      )}
      {f.tipo === "partes" && (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {f.partes.map((parte) => (
            <label key={parte.caminho} className="flex flex-col gap-1 text-sm font-medium">
              {parte.caminho}
              {parte.numerico ? " (número)" : ""}
              <input name={`parte:${parte.caminho}`} defaultValue={c.valores[`parte:${parte.caminho}`] ?? ""} inputMode={parte.numerico ? "decimal" : "text"} className={caixa} />
            </label>
          ))}
        </div>
      )}
      {c.validacao && <p className="text-sm text-tinta-2">Regra: {c.validacao}</p>}
      <Mensagem resultado={resultado} />
      <div>
        <Botao variante="secundario">Salvar {c.id}</Botao>
      </div>
    </form>
  );
}
