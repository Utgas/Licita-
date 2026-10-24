"use client";
/** Formulários da tela do checklist: envio do Word, resposta digitada, trava e complemento. */
import { useActionState } from "react";
import type { Resultado } from "@/auth/acoes.ts";
import { Botao, Mensagem } from "../../../componentes/formulario.tsx";

type Acao = (anterior: Resultado, dados: FormData) => Promise<Resultado>;

const caixa = "min-h-11 w-full rounded border border-zinc-500 px-3 py-2";

export function EnviarWord({ acao }: { acao: Acao }) {
  const [resultado, enviar] = useActionState(acao, null);
  return (
    <form action={enviar} className="flex flex-col gap-3">
      <label className="flex flex-col gap-1 text-sm font-medium">
        Checklist preenchido (.docx)
        <input type="file" name="arquivo" accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document" required className="min-h-11 font-normal" />
      </label>
      <p className="text-sm text-zinc-700">O arquivo é lido e descartado; fica só o hash. Um novo envio substitui as respostas daquele checklist.</p>
      <Mensagem resultado={resultado} />
      <div>
        <Botao>Ler o checklist</Botao>
      </div>
    </form>
  );
}

export type DadosDaPergunta = {
  pergunta: string;
  tipo: string;
  opcoes: string[];
  campos: string[];
  porItem: boolean;
  temNumero: boolean;
};

export type LinhaSalva = { id: number; valor: unknown; texto: string | null; numero: string | null; itens: number[] };

/** Resposta digitada ou corrigida (uma linha; por item, com os números dos itens). */
export function FormularioResposta({ acao, apagar, p, linha, confirmarMotivo }: { acao: Acao; apagar?: Acao; p: DadosDaPergunta; linha?: LinhaSalva; confirmarMotivo?: string }) {
  const [resultado, salvar] = useActionState(acao, null);
  const [apagado, apagarAcao] = useActionState(apagar ?? (async () => null), null);
  const atual = linha?.valor;
  const marcadas = new Set(Array.isArray(atual) ? atual.map(String) : typeof atual === "string" ? [atual] : []);
  const tabela = Array.isArray(atual) && typeof atual[0] === "object" ? (atual[0] as Record<string, string>) : {};
  return (
    <div className="flex flex-col gap-2 rounded border border-zinc-300 bg-white p-3">
      <form action={salvar} className="flex flex-col gap-3">
        <input type="hidden" name="pergunta" value={p.pergunta} />
        {linha && <input type="hidden" name="linha" value={linha.id} />}
        {confirmarMotivo && <input type="hidden" name="confirmarMotivo" value={confirmarMotivo} />}
        {(p.tipo === "SIM_NAO" || p.tipo === "UNICA") && (
          <fieldset className="flex flex-wrap gap-x-4">
            <legend className="text-sm font-medium">Resposta</legend>
            {p.opcoes.map((o) => (
              <label key={o} className="flex min-h-11 items-center gap-2">
                <input type="radio" name="valor" value={o} defaultChecked={marcadas.has(o)} className="size-5" /> {o}
              </label>
            ))}
            <label className="flex min-h-11 items-center gap-2 text-zinc-700">
              <input type="radio" name="valor" value="" defaultChecked={marcadas.size === 0} className="size-5" /> Sem resposta
            </label>
          </fieldset>
        )}
        {p.tipo === "MULTIPLA" && (
          <fieldset className="flex flex-wrap gap-x-4">
            <legend className="text-sm font-medium">Marque todas as que valem</legend>
            {p.opcoes.map((o) => (
              <label key={o} className="flex min-h-11 items-center gap-2">
                <input type="checkbox" name="valor" value={o} defaultChecked={marcadas.has(o)} className="size-5" /> {o}
              </label>
            ))}
          </fieldset>
        )}
        {p.tipo === "TABELA" &&
          p.campos.map((c) => (
            <label key={c} className="flex flex-col gap-1 text-sm font-medium">
              {c}
              <input name={`campo:${c}`} defaultValue={tabela[c] ?? ""} className={caixa} />
            </label>
          ))}
        {(p.tipo === "TEXTO" || p.tipo === "NUMERO") && (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Resposta
            <textarea name="valor" defaultValue={typeof atual === "string" ? atual : ""} rows={3} className={caixa} />
          </label>
        )}
        {p.tipo !== "TEXTO" && p.tipo !== "TABELA" && (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Texto da caixa &quot;Resposta:&quot; ou escrito ao lado de &quot;Outro&quot;
            <textarea name="texto" defaultValue={linha?.texto ?? ""} rows={2} className={caixa} />
          </label>
        )}
        {p.temNumero && (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Número do &quot;Outro&quot; (só algarismos)
            <input name="numero" inputMode="numeric" defaultValue={linha?.numero ?? ""} className={`${caixa} max-w-40`} />
          </label>
        )}
        {p.porItem && (
          <label className="flex flex-col gap-1 text-sm font-medium">
            Itens a que esta resposta se aplica (ex.: 1, 3 e 5; vazio = todos)
            <input name="itens" defaultValue={linha?.itens.join(", ") ?? ""} className={`${caixa} max-w-80`} />
          </label>
        )}
        <Mensagem resultado={resultado} />
        <div>
          <Botao>{confirmarMotivo ? "Salvar e confirmar" : "Salvar resposta"}</Botao>
        </div>
      </form>
      {linha && apagar && (
        <form action={apagarAcao}>
          <input type="hidden" name="linha" value={linha.id} />
          <Mensagem resultado={apagado} />
          <Botao variante="secundario">Apagar esta resposta</Botao>
        </form>
      )}
    </div>
  );
}

/** Trava: escolhe a resposta com um botão, ou confirma a que está. */
export function Trava({ acaoResposta, acaoConfirmar, pergunta, motivo, opcoes, outro }: { acaoResposta: Acao; acaoConfirmar: Acao; pergunta: string; motivo: string; opcoes: string[]; outro?: string }) {
  const [r1, responder] = useActionState(acaoResposta, null);
  const [r2, confirmar] = useActionState(acaoConfirmar, null);
  return (
    <div className="flex flex-col gap-2">
      {outro && (
        <form action={responder} className="flex flex-wrap items-end gap-2">
          <input type="hidden" name="pergunta" value={pergunta} />
          <input type="hidden" name="valor" value={outro} />
          <input type="hidden" name="confirmarMotivo" value={motivo} />
          <label className="flex flex-col gap-1 text-sm font-medium">
            Número do &quot;{outro}&quot; (só algarismos)
            <input name="numero" inputMode="numeric" required pattern="[0-9]+" className="min-h-11 w-40 rounded border border-zinc-500 px-3" />
          </label>
          <Botao>Salvar o número</Botao>
        </form>
      )}
      <div className="flex flex-wrap gap-2">
        {opcoes.map((o) => (
          <form key={o} action={responder}>
            <input type="hidden" name="pergunta" value={pergunta} />
            <input type="hidden" name="valor" value={o} />
            <input type="hidden" name="confirmarMotivo" value={motivo} />
            <Botao variante="secundario">{o}</Botao>
          </form>
        ))}
        <form action={confirmar}>
          <input type="hidden" name="pergunta" value={pergunta} />
          <input type="hidden" name="motivo" value={motivo} />
          <Botao variante="secundario">Conferi: vale como está</Botao>
        </form>
      </div>
      <Mensagem resultado={r1} />
      <Mensagem resultado={r2} />
    </div>
  );
}

/** Complemento do operador (CK-X): por processo ou item a item. */
export function Complemento({ acao, pergunta, tipo, opcoes, itens, valor }: { acao: Acao; pergunta: string; tipo: string; opcoes: string[]; itens: number[] | null; valor: unknown }) {
  const [resultado, salvar] = useActionState(acao, null);
  const mostrar = (v: unknown) => (Array.isArray(v) ? v.join(", ") : v === null || v === undefined ? "" : String(v));
  const campo = (nome: string, atual: unknown) =>
    tipo === "UNICA" ? (
      <select name={nome} defaultValue={mostrar(atual)} className={`${caixa} max-w-md`}>
        <option value="">Sem resposta</option>
        {opcoes.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    ) : tipo === "TEXTO" ? (
      <textarea name={nome} defaultValue={mostrar(atual)} rows={2} className={caixa} />
    ) : (
      <input name={nome} defaultValue={mostrar(atual)} inputMode={tipo === "NUMERO" ? "decimal" : "text"} placeholder={tipo === "MULTIPLA" ? "Números dos itens, ex.: 1, 3 e 5" : ""} className={`${caixa} max-w-md`} />
    );
  return (
    <form action={salvar} className="flex flex-col gap-2">
      <input type="hidden" name="pergunta" value={pergunta} />
      {itens === null ? (
        campo("valor", valor)
      ) : itens.length === 0 ? (
        <p className="text-zinc-700">Cadastre os itens primeiro: este complemento é respondido item a item.</p>
      ) : (
        itens.map((n) => (
          <label key={n} className="flex flex-col gap-1 text-sm font-medium">
            Item {n}
            {campo(`item:${n}`, (valor as Record<string, unknown> | null)?.[String(n)])}
          </label>
        ))
      )}
      <Mensagem resultado={resultado} />
      <div>
        <Botao>Salvar complemento</Botao>
      </div>
    </form>
  );
}
