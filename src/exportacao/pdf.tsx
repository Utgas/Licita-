/**
 * PDF da minuta (passo 11): gerado no servidor com @react-pdf/renderer, entregue na hora e nunca guardado; só o hash
 * vai para a auditoria (arquitetura, "Segurança e retenção"). Fontes padrão do PDF (Helvetica), sem fonte nem imagem
 * de terceiros. O cabeçalho tem só o espaço do brasão, com um marcador neutro (o brasão não entra no repositório).
 * O texto é o da minuta: lacuna sai marcada, valor padrão sai sem a marca.
 */
import { Document, Page, StyleSheet, Text, View, renderToBuffer } from "@react-pdf/renderer";
import type { Minuta } from "../motor/minuta.ts";
import { ehTabela, linhasDaTabela, secoesDaMinuta, tabelaNaoMontada, textoFinal } from "./secoes.ts";

const estilos = StyleSheet.create({
  pagina: { paddingTop: 40, paddingBottom: 56, paddingHorizontal: 48, fontFamily: "Helvetica", fontSize: 10.5 },
  cabecalho: { flexDirection: "row", alignItems: "center", marginBottom: 16, gap: 12 },
  brasao: { width: 44, height: 44, borderWidth: 1, borderStyle: "dashed", borderColor: "#666", alignItems: "center", justifyContent: "center" },
  brasaoTexto: { fontSize: 6, color: "#666" },
  om: { fontSize: 9, flexGrow: 1 },
  aviso: { fontSize: 8, color: "#444", borderWidth: 1, borderColor: "#999", padding: 4, marginBottom: 12 },
  // Entrelinha no parágrafo, não na página: na página, com o número de página (render), a paginação quebra.
  paragrafo: { marginBottom: 6, textAlign: "justify", lineHeight: 1.4 },
  numero: { fontFamily: "Helvetica-Bold" },
  tabela: { borderWidth: 0.5, borderColor: "#333", marginBottom: 8 },
  linha: { flexDirection: "row", borderBottomWidth: 0.5, borderColor: "#333" },
  celula: { flex: 1, padding: 3, fontSize: 8, borderRightWidth: 0.5, borderColor: "#333" },
  celulaTitulo: { fontFamily: "Helvetica-Bold" },
  rodape: { position: "absolute", bottom: 24, left: 48, right: 120, fontSize: 7.5, color: "#444" },
  numeroDaPagina: { position: "absolute", bottom: 24, right: 48, fontSize: 7.5, color: "#444" },
});

export type DadosDoPdf = {
  minuta: Minuta;
  numeroDoProcesso: string;
  cabecalhoDaOm: string[];
};

function DocumentoDaMinuta({ minuta, numeroDoProcesso, cabecalhoDaOm }: DadosDoPdf) {
  const lacunas = minuta.lacunasNoTexto.length;
  return (
    <Document title={`Minuta de TR - ${numeroDoProcesso}`} author="Licita+" creator="Licita+" producer="Licita+">
      <Page size="A4" style={estilos.pagina} wrap>
        <View style={estilos.cabecalho} fixed>
          <View style={estilos.brasao}>
            <Text style={estilos.brasaoTexto}>brasão</Text>
          </View>
          <Text style={estilos.om}>{cabecalhoDaOm.join("\n")}</Text>
        </View>
        <Text style={estilos.aviso}>
          MINUTA para revisão humana antes de usar no Compras.gov.br. Processo {numeroDoProcesso}.{lacunas > 0 ? ` Há ${lacunas} lacuna(s) marcada(s) como [LACUNA] a completar.` : ""}
        </Text>
        {secoesDaMinuta(minuta).flatMap((s) =>
          s.trechos.map((t) => {
            if (ehTabela(t)) {
              const linhas = linhasDaTabela(t.texto);
              return (
                <View key={t.id}>
                  {tabelaNaoMontada(t.texto).naoMontada && <Text style={estilos.paragrafo}>[LACUNA: tabela não montada]</Text>}
                  <View style={estilos.tabela}>
                    {linhas.map((linha, k) => (
                      <View key={k} style={estilos.linha} wrap={false}>
                        {linha.map((c, j) => (
                          <Text key={j} style={k === 0 ? [estilos.celula, estilos.celulaTitulo] : estilos.celula}>
                            {textoFinal(c)}
                          </Text>
                        ))}
                      </View>
                    ))}
                  </View>
                </View>
              );
            }
            return (
              <Text key={t.id} style={estilos.paragrafo}>
                {t.numero ? <Text style={estilos.numero}>{t.numero} </Text> : null}
                {textoFinal(t.texto)}
              </Text>
            );
          }),
        )}
        <Text style={estilos.rodape} fixed>
          Licita+ · pacote {minuta.pacote.pacote} ({minuta.pacote.hash.slice(0, 12)})
        </Text>
        
        <Text style={estilos.numeroDaPagina} fixed render={({ pageNumber, totalPages }) => `${pageNumber} / ${totalPages}`} />
      </Page>
    </Document>
  );
}

export async function gerarPdf(dados: DadosDoPdf): Promise<Buffer> {
  return renderToBuffer(<DocumentoDaMinuta {...dados} />);
}
