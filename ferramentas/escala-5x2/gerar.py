"""Gera a escala 5x2 (30/11/2026 a 03/01/2027) em Excel, Word e PDF.

Uso (na raiz do projeto):
    python3 ferramentas/escala-5x2/gerar.py

Os arquivos saem em escalas/2026-12_2027-01/.
Precisa de Python 3 com ortools, openpyxl e python-docx; o PDF usa o LibreOffice.
"""

import collections
import os
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from conferencia import conferir  # noqa: E402
from exportar_excel import gerar_excel  # noqa: E402
from exportar_word import gerar_word  # noqa: E402
from otimizador import montar_escala  # noqa: E402

PASTA = os.path.normpath(os.path.join(AQUI, "..", "..", "escalas", "2026-12_2027-01"))
NOME = "escala-5x2-dez2026-jan2027"


def main():
    os.makedirs(PASTA, exist_ok=True)
    print("Montando a escala...")
    escala, situacao = montar_escala()
    for setor, (pontos, status) in situacao.items():
        print(f"  {setor}: {status}, {pontos:.0f} pontos de problema")

    ocorrencias = conferir(escala)
    print("Conferência:", dict(collections.Counter(o["tipo"] for o in ocorrencias)))

    xlsx = os.path.join(PASTA, NOME + ".xlsx")
    docx = os.path.join(PASTA, NOME + ".docx")
    abas = gerar_excel(xlsx, escala, ocorrencias)
    gerar_word(docx, escala, ocorrencias)
    print("Excel:", ", ".join(abas))
    print("Word gerado")

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", PASTA, docx],
                       check=True, capture_output=True)
        print("PDF gerado")
    else:
        print("LibreOffice não encontrado: PDF não gerado")


if __name__ == "__main__":
    main()
