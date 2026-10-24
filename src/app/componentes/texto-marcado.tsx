/**
 * Texto do motor com as marcas pintadas (minuta do TR e ETP): lacuna em amarelo, valor padrão em azul; tabela em
 * linhas e colunas. Só apresentação: o texto vem pronto do motor.
 */
import { linhasDaTabela, partesDoTexto, tabelaNaoMontada } from "@/exportacao/secoes.ts";
import { Icone } from "./icones.tsx";

export function TextoMarcado({ texto }: { texto: string }) {
  return (
    <>
      {partesDoTexto(texto).map((parte, k) =>
        parte.tipo === "texto" ? (
          <span key={k}>{parte.texto}</span>
        ) : parte.tipo === "lacuna" ? (
          <mark key={k} className="inline-flex items-baseline gap-1 bg-atencao-marca px-1 text-atencao">
            <Icone nome="lacuna" tamanho={13} className="self-center" />
            {parte.texto}
          </mark>
        ) : (
          <mark key={k} className="bg-padrao-fundo px-0.5 text-padrao underline decoration-dotted underline-offset-4" title="Valor padrão do pacote: confira">
            {parte.texto}
          </mark>
        ),
      )}
    </>
  );
}

/** Tabela do motor: primeira linha é o cabeçalho, colunas separadas por " | ". */
export function TabelaMarcada({ texto }: { texto: string }) {
  return (
    <div className="overflow-x-auto">
      {tabelaNaoMontada(texto).naoMontada && (
        <p>
          <mark className="inline-flex items-center gap-1 bg-atencao-marca px-1 text-atencao">
            <Icone nome="lacuna" tamanho={13} />
            tabela não montada: faltam as linhas (veja a origem)
          </mark>
        </p>
      )}
      <table className="w-full border-collapse text-left text-sm">
        <tbody>
          {linhasDaTabela(texto).map((linha, k) => (
            <tr key={k} className={k === 0 ? "border-b-2 border-linha-forte font-semibold" : "border-b border-linha"}>
              {linha.map((c, j) => (
                <td key={j} className="p-2 align-top whitespace-pre-line">
                  <TextoMarcado texto={c} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
