#!/usr/bin/env python3
"""Fase 0 - Extracao de texto de todos os arquivos da base Licita+.

Uso: python3 -I f0_extrair_texto.py <pasta_Documentos> <pasta_saida> <tessdata_dir>

Para cada PDF:
  - pdftotext (modo layout e modo fluxo), uma pasta por documento, um arquivo por pagina;
  - contagem de caracteres por pagina e lista de imagens por pagina (pdfimages -list);
  - pagina sem camada de texto (< 20 caracteres nao brancos) e rasterizada a 300 dpi e
    passa por OCR (tesseract, idioma por), com confianca media registrada.
Para DOCX: texto dos paragrafos de word/document.xml e contagem de comentarios.
Para MD: copia do texto.
Gera <pasta_saida>/_extracao.json com as metricas por arquivo e pagina.
"""
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

MIN_CHARS = 20  # abaixo disso a pagina e tratada como sem camada de texto
# pagina com imagem grande (>= 500 mil pixels) e pouco texto (< 300 caracteres) tambem passa por OCR:
# e o caso de paginas digitalizadas inseridas dentro de um PDF nativo (formato MISTO)
IMG_GRANDE = 500_000
CHARS_MISTO = 300


def run(cmd, env=None):
    r = subprocess.run(cmd, capture_output=True, env=env)
    return r.returncode, r.stdout, r.stderr


def slug(rel):
    s = re.sub(r"[^A-Za-z0-9]+", "_", rel).strip("_")
    return s[:120]


def pdf_pages(path):
    code, out, _ = run(["pdfinfo", str(path)])
    m = re.search(rb"Pages:\s+(\d+)", out)
    return int(m.group(1)) if m else 0


def pdf_images_per_page(path):
    code, out, _ = run(["pdfimages", "-list", str(path)])
    per = {}
    for line in out.decode("utf-8", "replace").splitlines()[2:]:
        parts = line.split()
        if len(parts) > 4 and parts[0].isdigit():
            pg = int(parts[0])
            per.setdefault(pg, []).append({"w": int(parts[3]), "h": int(parts[4]), "tipo": parts[2]})
    return per


def ocr_page(pdf, page, outdir, tessdata):
    png_base = outdir / f"ocr_p{page:03d}"
    run(["pdftoppm", "-r", "300", "-gray", "-f", str(page), "-l", str(page), "-png", "-singlefile", str(pdf), str(png_base)])
    png = Path(str(png_base) + ".png")
    env = dict(os.environ, TESSDATA_PREFIX=tessdata)
    # texto
    run(["tesseract", str(png), str(outdir / f"ocr_p{page:03d}"), "-l", "por", "--psm", "3"], env=env)
    # tsv para confianca
    run(["tesseract", str(png), str(outdir / f"ocr_p{page:03d}"), "-l", "por", "--psm", "3", "tsv"], env=env)
    txt = (outdir / f"ocr_p{page:03d}.txt").read_text(encoding="utf-8", errors="replace")
    confs = []
    tsv = outdir / f"ocr_p{page:03d}.tsv"
    if tsv.exists():
        for i, line in enumerate(tsv.read_text(encoding="utf-8", errors="replace").splitlines()):
            if i == 0:
                continue
            cols = line.split("\t")
            if len(cols) >= 12 and cols[11].strip():
                try:
                    c = float(cols[10])
                except ValueError:
                    continue
                if c >= 0:
                    confs.append(c)
    png.unlink(missing_ok=True)
    mean = round(sum(confs) / len(confs), 1) if confs else None
    return txt, mean, len(confs)


def extract_pdf(pdf, outdir, tessdata):
    outdir.mkdir(parents=True, exist_ok=True)
    n = pdf_pages(pdf)
    imgs = pdf_images_per_page(pdf)
    _, lay, _ = run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"])
    _, raw, _ = run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"])
    lay_pages = lay.decode("utf-8", "replace").split("\f")
    raw_pages = raw.decode("utf-8", "replace").split("\f")
    pages = []
    full = []
    for p in range(1, n + 1):
        t_lay = lay_pages[p - 1] if p - 1 < len(lay_pages) else ""
        t_raw = raw_pages[p - 1] if p - 1 < len(raw_pages) else ""
        nchars = len(re.sub(r"\s+", "", t_raw))
        info = {"pagina": p, "chars_texto": nchars, "imagens": imgs.get(p, []), "ocr": False,
                "ocr_conf_media": None, "ocr_palavras": 0}
        texto = t_lay
        maior_img = max([i["w"] * i["h"] for i in imgs.get(p, [])] or [0])
        if nchars < MIN_CHARS or (maior_img >= IMG_GRANDE and nchars < CHARS_MISTO):
            txt, mean, nw = ocr_page(pdf, p, outdir, tessdata)
            info.update({"ocr": True, "ocr_conf_media": mean, "ocr_palavras": nw,
                         "chars_ocr": len(re.sub(r"\s+", "", txt)),
                         "motivo_ocr": "sem_camada_texto" if nchars < MIN_CHARS else "imagem_grande_pouco_texto"})
            texto = (t_lay.strip() + "\n[--- OCR ---]\n" + txt) if nchars >= MIN_CHARS else txt
        (outdir / f"p{p:03d}.txt").write_text(texto, encoding="utf-8")
        (outdir / f"p{p:03d}_fluxo.txt").write_text(t_raw if not info["ocr"] else texto, encoding="utf-8")
        full.append(f"\n===== PAGINA {p} de {n} =====\n{texto}")
        pages.append(info)
    (outdir / "_completo.txt").write_text("".join(full), encoding="utf-8")
    return {"paginas_pdf": n, "paginas": pages}


def extract_docx(docx, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(docx)
    names = z.namelist()
    doc = z.read("word/document.xml").decode("utf-8")
    paras = re.findall(r"<w:p[ >].*?</w:p>", doc, flags=re.S)
    textos = []
    for p in paras:
        t = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", p, flags=re.S))
        textos.append(t)
    (outdir / "_completo.txt").write_text("\n".join(textos), encoding="utf-8")
    n_com = 0
    if "word/comments.xml" in names:
        com = z.read("word/comments.xml").decode("utf-8")
        n_com = len(re.findall(r"<w:comment ", com))
    n_range = len(re.findall(r"<w:commentRangeStart ", doc))
    n_ref = len(re.findall(r"<w:commentReference ", doc))
    rodapes = {}
    for n in names:
        if re.match(r"word/footer\d*\.xml", n):
            x = z.read(n).decode("utf-8")
            rodapes[n] = "".join(re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", x, flags=re.S))
    return {"paragrafos_xml": len(paras), "paragrafos_nao_vazios": sum(1 for t in textos if t.strip()),
            "comentarios": n_com, "commentRangeStart": n_range, "commentReference": n_ref,
            "rodapes": rodapes, "partes": names}


def main():
    base = Path(sys.argv[1])
    out = Path(sys.argv[2])
    tessdata = sys.argv[3]
    out.mkdir(parents=True, exist_ok=True)
    result = {}
    for f in sorted(base.rglob("*")):
        if not f.is_file():
            continue
        rel = str(f.relative_to(base))
        d = out / slug(rel)
        if f.suffix.lower() == ".pdf":
            result[rel] = {"tipo_arquivo": "pdf", "dir": str(d), **extract_pdf(f, d, tessdata)}
        elif f.suffix.lower() == ".docx":
            result[rel] = {"tipo_arquivo": "docx", "dir": str(d), **extract_docx(f, d)}
        elif f.suffix.lower() == ".md":
            d.mkdir(parents=True, exist_ok=True)
            txt = f.read_text(encoding="utf-8", errors="replace")
            (d / "_completo.txt").write_text(txt, encoding="utf-8")
            result[rel] = {"tipo_arquivo": "md", "dir": str(d), "linhas": txt.count("\n") + 1}
        else:
            result[rel] = {"tipo_arquivo": f.suffix.lower() or "sem_extensao", "dir": None}
        print("ok", rel, flush=True)
    (out / "_extracao.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
