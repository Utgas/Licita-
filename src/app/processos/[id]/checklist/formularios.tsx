"use client";
/** Formulários da tela do checklist: envio do Word ou do PDF, resposta digitada, trava e complemento. */
import { useActionState, useId, useRef, useState } from "react";
import type { Resultado } from "@/auth/acoes.ts";
import { Botao, Mensagem } from "../../../componentes/formulario.tsx";
import { Icone } from "../../../componentes/icones.tsx";
import { classesDoBotao } from "../../../componentes/ui.tsx";

type Acao = (anterior: Resultado, dados: FormData) => Promise<Resultado>;

const caixa = "min-h-11 w-full rounded-sm border border-linha-forte px-3 py-2";

/** Limite do envio (o mesmo da ação no servidor): conferido aqui para o aviso sair antes do envio. */
const TAMANHO_MAXIMO = 4 * 1024 * 1024;

/**
 * Espaço de um checklist: "Anexar" abre a escolha do arquivo; escolhido o arquivo, o botão passa a ser "Ler". O
 * checklist esperado vai junto, para o servidor recusar o arquivo do outro checklist com uma mensagem clara.
 */
export function EnviarChecklist({ acao, checklist, nome, jaLido }: { acao: Acao; checklist: "CONSUMO" | "PERMANENTES"; nome: string; jaLido: boolean }) {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const entrada = useRef<HTMLInputElement>(null);
  // Lido o arquivo, o espaço volta ao "Anexar" (o resultado fica na mensagem).
  const [resultado, enviar] = useActionState(async (anterior: Resultado, dados: FormData) => {
    const r = await acao(anterior, dados);
    if (r?.aviso) {
      setArquivo(null);
      if (entrada.current) entrada.current.value = "";
    }
    return r;
  }, null);
  const id = useId();
  const grande = arquivo !== null && arquivo.size > TAMANHO_MAXIMO;
  const escolher = () => entrada.current?.click();
  return (
    <form action={enviar} className="flex flex-col gap-3">
      <input type="hidden" name="checklist" value={checklist} />
      <input
        ref={entrada}
        id={id}
        type="file"
        name="arquivo"
        accept=".docx,.odt,.pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.oasis.opendocument.text,application/pdf"
        className="sr-only"
        tabIndex={-1}
        onChange={(e) => setArquivo(e.currentTarget.files?.[0] ?? null)}
      />
      {arquivo === null ? (
        <div>
          <button type="button" onClick={escolher} className={classesDoBotao(jaLido ? "secundario" : "principal")}>
            <Icone nome="documento" tamanho={16} /> {jaLido ? `Anexar outro checklist de ${nome}` : `Anexar checklist de ${nome}`}
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          <p className="text-sm">
            Arquivo escolhido: <strong>{arquivo.name}</strong> ({(arquivo.size / 1024 / 1024).toFixed(1).replace(".", ",")} MB)
          </p>
          {grande && (
            <p className="flex items-start gap-2 text-sm text-trava">
              <Icone nome="trava" className="mt-0.5" /> Arquivo maior que 4 MB. Tire as imagens coladas no documento e escolha de novo.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            {!grande && <Botao>Ler o checklist de {nome}</Botao>}
            <button type="button" onClick={escolher} className={classesDoBotao("discreto")}>
              Trocar arquivo
            </button>
          </div>
        </div>
      )}
      <Mensagem resultado={resultado} />
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
    <div className="flex flex-col gap-2 rounded-sm border border-linha bg-folha p-3">
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
            <label className="flex min-h-11 items-center gap-2 text-tinta-2">
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
            <input name="numero" inputMode="numeric" required pattern="[0-9]+" className="min-h-11 w-40 rounded-sm border border-linha-forte px-3" />
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
        <p className="text-tinta-2">Cadastre os itens primeiro: este complemento é respondido item a item.</p>
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
