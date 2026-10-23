#!/usr/bin/env python3
"""Fase 0 - Conferencias por script que sustentam o inventario (M00) e os achados da secao 5.

Uso: python3 -I f0_inventario_apoio.py <pasta_Documentos> <pasta_texto> <modelo_estrutura.json> <saida.txt>

Gera um relatorio de texto com:
  1. paginacao: rodape 'X de N' de cada PDF comparado com o numero real de paginas;
  2. versao do modelo AGU estampada no rodape de cada TR ('Atualizacao: MMM/AAAA');
  3. comentarios do modelo AGU: quantidade, ids, ancoras (inicio e fim) e ancoras de comprimento zero;
  4. alinhamento das referencias de 'Linhas' da matriz 01 com a numeracao de paragrafos do docx;
  5. ocorrencias de 'nota' e de '~' nas matrizes 01 e 02;
  6. titulos de secao dos ETPs (quantidade e nome da secao 12);
  7. codigos de 6 digitos (padrao CATMAT) em comum entre ETPs e TR 190/2025;
  8. citacoes de normas do regime anterior ou a conferir;
  9. percentuais de validade minima (50% e 75%) por documento e pagina.
Nomes de arquivo que contem nomes de pessoas saem com [NOME] (mesma regra do M00).
"""
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

NOME_REGISTRADO = {}  # vazio desde a Fase 1 (arquivo do ETP 58/2025 renomeado, P01)


def registrado(nome):
    for pref, reg in NOME_REGISTRADO.items():
        if nome.startswith(pref):
            return reg
    return nome


def slug(rel):
    return re.sub(r"[^A-Za-z0-9]+", "_", rel).strip("_")[:120]


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def paginas(dirdoc):
    return sorted(dirdoc.glob("p[0-9][0-9][0-9].txt"))


def main():
    base = Path(sys.argv[1])
    textos = Path(sys.argv[2])
    estrutura = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    out = []
    pdfs = sorted(p for p in base.rglob("*.pdf"))

    # 1. paginacao
    out.append("## 1. Paginação (rodapé 'X de N' x páginas do arquivo)")
    for pdf in pdfs:
        rel = str(pdf.relative_to(base))
        d = textos / slug(rel)
        res = []
        for f in paginas(d):
            t = f.read_text(encoding="utf-8").strip()
            ms = [m for m in re.findall(r"(\d{1,2})\s?de\s?(\d{1,2})\s*$", t, flags=re.M) if int(m[1]) >= int(m[0])]
            res.append(f"{ms[-1][0]}/{ms[-1][1]}" if ms else "-")
        n = len(res)
        ok = all(r == f"{i + 1}/{n}" for i, r in enumerate(res))
        out.append(f"{'OK ' if ok else 'VER'} {registrado(pdf.name)}: {n} páginas no arquivo; rodapés lidos: {' '.join(res)}")
    out.append("Obs.: rodapés '-' em páginas OCR sem número reconhecido foram conferidos na imagem.")

    # 2. versao AGU nos TRs
    out.append("\n## 2. Versão do modelo AGU no rodapé dos TRs")
    for pdf in pdfs:
        t = (textos / slug(str(pdf.relative_to(base))) / "_completo.txt").read_text(encoding="utf-8")
        vers = sorted(set(re.findall(r"Atualização: ?([A-Z]{3}/\d{4})", t)))
        if vers:
            out.append(f"{registrado(pdf.name)}: {', '.join(vers)} ({len(re.findall(r'Atualização: ?[A-Z]{3}/[0-9]{4}', t))} rodapés)")

    # 3. comentarios do modelo
    out.append("\n## 3. Notas explicativas (comentários) do modelo AGU")
    docx = next(base.rglob("modelo-de-termo-de-referencia*.docx"))
    z = zipfile.ZipFile(docx)
    doc = z.read("word/document.xml").decode("utf-8")
    com = z.read("word/comments.xml").decode("utf-8")
    ids = re.findall(r'<w:comment [^>]*w:id="(\d+)"', com)
    sem, vazios = [], []
    for cid in ids:
        s = re.search(rf'<w:commentRangeStart w:id="{cid}"/>', doc)
        e = re.search(rf'<w:commentRangeEnd w:id="{cid}"/>', doc)
        if not s or not e:
            sem.append(cid)
            continue
        txt = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", doc[s.end():e.start()]))
        if not txt.strip():
            vazios.append(cid)
    rodape = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", "".join(z.read(n).decode("utf-8") for n in z.namelist() if n.startswith("word/footer"))))
    out.append(f"comentários: {len(ids)}; ids de {min(map(int, ids))} a {max(map(int, ids))}")
    out.append(f"sem commentRangeStart ou commentRangeEnd: {sem or 'nenhum'}")
    out.append(f"âncoras de comprimento zero (sem texto entre início e fim): {vazios}")
    out.append(f"rodapé contém 'Atualização: DEZ/2025': {'Atualização: DEZ/2025' in rodape}")
    out.append(f"parágrafos no corpo: {estrutura['paragrafos_total']}; não vazios: {estrutura['paragrafos_nao_vazios']}; dentro de tabelas: {estrutura['paragrafos_em_tabela']}")

    # 4. alinhamento matriz 01 x paragrafos do docx
    out.append("\n## 4. Matriz 01: referências de 'Linhas' x parágrafos do docx DEZ/2025")
    m01 = next(base.rglob("01_Matriz_TR_AGU_Aquisicoes.md")).read_text(encoding="utf-8")
    P = estrutura["paragrafos"]
    refs = []
    titulo = ""
    for linha in m01.splitlines():
        h = re.match(r"^###\s+[\d.]+\s+(.*?)\s*\((Linhas?)\s+(\d+)(?:-(\d+))?\)", linha)
        if h:
            refs.append((h.group(1), int(h.group(3)), int(h.group(4) or h.group(3))))
            continue
        for m in re.finditer(r"\(linhas?\s+(\d+)(?:-(\d+))?\)", linha, flags=re.I):
            campo = linha.split("|")[2].strip() if linha.count("|") > 3 else linha[:40]
            refs.append((campo, int(m.group(1)), int(m.group(2) or m.group(1))))
    alinhados = 0
    for nome, a, b in refs:
        trecho = " ".join(P[i]["texto"] for i in range(a - 1, min(b, len(P))))
        palavras = {w for w in re.findall(r"[a-z]{5,}", sem_acento(nome))}
        hit = palavras & set(re.findall(r"[a-z]{5,}", sem_acento(trecho)))
        alinhados += bool(hit)
        out.append(f"{'OK ' if hit else 'VER'} [{a}-{b}] {nome} -> início: {P[a - 1]['texto'][:70]!r}")
    out.append(f"intervalos com palavra do título no trecho referido: {alinhados} de {len(refs)} "
               f"(os marcados VER pedem leitura: o título usa sigla, plural ou sinônimo do texto do modelo)")

    # 5. 'nota' e '~' nas matrizes
    out.append("\n## 5. Matrizes 01 e 02: ocorrências")
    for nome in ("01_Matriz_TR_AGU_Aquisicoes.md", "02_Matriz_ETP_Digital_Lei14133.md"):
        t = next(base.rglob(nome)).read_text(encoding="utf-8")
        out.append(f"{nome}: 'nota' {len(re.findall(r'nota', t, flags=re.I))}x; '~' {t.count('~')}x; "
                   f"'media_1792606488039_644bd1c3.docx' {t.count('media_1792606488039_644bd1c3.docx')}x")

    # 6. secoes dos ETPs
    out.append("\n## 6. ETPs: títulos de seção")
    pat = re.compile(r"^\s{0,3}(\d{1,2})\.\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n]{2,90})$")
    for pdf in pdfs:
        d = textos / slug(str(pdf.relative_to(base)))
        t1 = (d / "p001.txt").read_text(encoding="utf-8")
        if not re.search(r"Estudo Técnico Preliminar \d+/\d{4}", t1):
            continue
        secoes = []
        for f in paginas(d):
            for linha in f.read_text(encoding="utf-8").splitlines():
                m = pat.match(linha)
                if m and not linha.strip().endswith((".", ";", ",")) and len(m.group(2)) < 70 and m.group(2)[0].isupper() \
                        and not re.search(r"\b(de|da|do|para|que)$", m.group(2).strip()):
                    secoes.append((int(m.group(1)), re.sub(r"\s{2,}.*$", "", m.group(2).strip()), int(f.stem[1:])))
        secoes = [s for s in secoes if not (s[0] > 20)]
        nums = [s[0] for s in secoes]
        s12 = [s[1] for s in secoes if s[0] == 12]
        ultima = secoes[-1] if secoes else None
        out.append(f"{registrado(pdf.name)}: {len(secoes)} títulos; números {nums}; seção 12 = {s12}; última = {ultima[0]}. {ultima[1]}")

    # 7. codigos de 6 digitos
    out.append("\n## 7. Códigos de 6 dígitos (padrão CATMAT) em comum")
    alvos = {"ETP 99/2025": "d4ef8f94", "ETP 151/2025": "ed187742", "ETP 801/2025": "08955b4e",
             "ETP 330/2025": "fdace9da", "TR 190/2025": "1e19dfeb"}
    cods = {}
    for rot, pref in alvos.items():
        pdf = next(p for p in pdfs if p.name.startswith(pref))
        t = (textos / slug(str(pdf.relative_to(base))) / "_completo.txt").read_text(encoding="utf-8")
        cods[rot] = set(re.findall(r"(?<![\d.,/])(\d{6})(?![\d.,/])", t))
        out.append(f"{rot}: {len(cods[rot])} códigos distintos")
    rots = list(alvos)
    for i, a in enumerate(rots):
        for b in rots[i + 1:]:
            out.append(f"{a} x {b}: {len(cods[a] & cods[b])} em comum")

    # 8. normas a conferir
    out.append("\n## 8. Citações de normas do regime anterior ou a conferir")
    padroes = {
        "Lei 10.520/2002": r"Lei\s*(?:n[º°o.]*\s*)?10\.520",
        "Decreto 10.024/2019": r"Decreto\s*(?:n[º°o.]*\s*)?10\.024",
        "Lei 8.666/1993": r"Lei\s*(?:n[º°o.]*\s*)?8\.666",
        "Decreto 7.892/2013": r"Decreto\s*(?:n[º°o.]*\s*)?7\.892",
        "IN SLTI/MP 01/2010": r"(?:IN|Instrução\s+Normativa)[^.]{0,40}?(?:n[º°o.]*\s*)?0?1[,/\s]+(?:de\s+19\s+de\s+janeiro\s+de\s+)?2010|IN\s+0?1/2010",
    }
    fontes = list(pdfs) + list(base.rglob("*.md"))
    for norma, rx in padroes.items():
        achados = []
        for f in fontes:
            if f.suffix == ".pdf":
                d = textos / slug(str(f.relative_to(base)))
                for pg in paginas(d):
                    if re.search(rx, pg.read_text(encoding="utf-8"), flags=re.I):
                        achados.append(f"{registrado(f.name)} p.{int(pg.stem[1:])}")
            else:
                for i, linha in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if re.search(rx, linha, flags=re.I):
                        achados.append(f"{f.name} linha {i}")
        out.append(f"{norma}: {len(achados)} ocorrência(s): {'; '.join(achados) or '-'}")

    # 9. validade minima
    out.append("\n## 9. Validade mínima na entrega: menções a 50% e 75%")
    for pdf in pdfs:
        d = textos / slug(str(pdf.relative_to(base)))
        hits = []
        for pg in paginas(d):
            t = pg.read_text(encoding="utf-8")
            for m in re.finditer(r"[^.\n]{0,90}\b(50|75)\s?%[^.\n]{0,60}", t):
                if re.search(r"validade|vida útil", m.group(0), flags=re.I):
                    hits.append(f"p.{int(pg.stem[1:])}: {m.group(1)}%")
        if hits:
            out.append(f"{registrado(pdf.name)}: {', '.join(hits)}")

    Path(sys.argv[4]).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
