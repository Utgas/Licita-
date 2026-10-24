import { redirect } from "next/navigation";
import { Suspense } from "react";
import { abrirProcesso } from "@/dados/acesso-processo.ts";
import { Carregando } from "../../componentes/cabecalho.tsx";
import { ETAPAS } from "../../componentes/rotulos.ts";

export default function Processo({ params }: PageProps<"/processos/[id]">) {
  return (
    <Suspense fallback={<Carregando />}>
      <Encaminhar params={params} />
    </Suspense>
  );
}

async function Encaminhar({ params }: Pick<PageProps<"/processos/[id]">, "params">): Promise<null> {
  const { id } = await params;
  const { p } = await abrirProcesso(id);
  redirect(`/processos/${id}/${(ETAPAS.find((e) => e.codigo === p.processo.etapa) ?? ETAPAS[0]).caminho}`);
}
